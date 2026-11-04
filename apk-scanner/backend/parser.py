"""Ekstraksi statis APK dengan Androguard 4.1.4. Tidak ada yang dijalankan; hanya membaca isi arsip."""
import hashlib
import re
import zipfile
from urllib.parse import urlsplit

from loguru import logger

from androguard.core.apk import APK
from androguard.core.axml import AXMLPrinter
from androguard.core.dex import DEX

logger.remove()  # androguard mencetak log debug sangat banyak ke stderr

NS = "{http://schemas.android.com/apk/res/android}"
URL_RE = re.compile(r"https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+")
IPV4_RE = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}")
IP_ONLY_RE = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}(?::\d{1,5})?")
RAW_SCAN_LIMIT = 5 * 1024 * 1024  # resource/asset lebih besar dari ini dilewati agar scan tetap cepat
EICAR_SCAN_LIMIT = 1024 * 1024    # EICAR hanya 68 byte; berkas besar tidak perlu dibaca utuh
EICAR = rb"X5O!P%@AP[4\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"
MAGIC = {b"PK\x03\x04": "zip", b"dex\n": "dex", b"\x7fELF": "elf"}  # isi yang bisa dipasang/dimuat sebagai kode
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")
LAUNCH_MODE = {"0": "standard", "1": "singleTop", "2": "singleTask", "3": "singleInstance"}  # AXML menyimpan enum sebagai angka

# Izin protectionLevel "dangerous" di AOSP + izin khusus yang sering disalahgunakan. Daftar tetap, karena
# get_details_permissions() androguard menganggap izin yang tidak ia kenali "dangerous" (mis. INTERNET pada APK lama).
DANGEROUS = {"android.permission." + p for p in (
    "READ_CALENDAR", "WRITE_CALENDAR", "CAMERA", "READ_CONTACTS", "WRITE_CONTACTS", "GET_ACCOUNTS",
    "ACCESS_FINE_LOCATION", "ACCESS_COARSE_LOCATION", "ACCESS_BACKGROUND_LOCATION", "RECORD_AUDIO",
    "READ_PHONE_STATE", "READ_PHONE_NUMBERS", "CALL_PHONE", "ANSWER_PHONE_CALLS", "READ_CALL_LOG", "WRITE_CALL_LOG",
    "ADD_VOICEMAIL", "USE_SIP", "PROCESS_OUTGOING_CALLS", "BODY_SENSORS", "BODY_SENSORS_BACKGROUND",
    "ACTIVITY_RECOGNITION", "SEND_SMS", "RECEIVE_SMS", "READ_SMS", "RECEIVE_WAP_PUSH", "RECEIVE_MMS",
    "READ_EXTERNAL_STORAGE", "WRITE_EXTERNAL_STORAGE", "READ_MEDIA_IMAGES", "READ_MEDIA_VIDEO", "READ_MEDIA_AUDIO",
    "POST_NOTIFICATIONS", "NEARBY_WIFI_DEVICES", "BLUETOOTH_SCAN", "BLUETOOTH_CONNECT", "BLUETOOTH_ADVERTISE",
    # khusus (bukan "dangerous" resmi, tetapi berisiko tinggi untuk pengguna awam)
    "SYSTEM_ALERT_WINDOW", "REQUEST_INSTALL_PACKAGES", "WRITE_SETTINGS", "MANAGE_EXTERNAL_STORAGE",
)}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _raw_texts(path):
    """Teks dari resources.arsc, assets, dan pustaka native (lib/): tempat token/URL pelaku sering disimpan selain di DEX."""
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            if (info.filename == "resources.arsc" or info.filename.startswith(("assets/", "lib/"))) and info.file_size <= RAW_SCAN_LIMIT:
                data = z.read(info)
                # string pool arsc bisa UTF-8 atau UTF-16
                yield data.decode("latin-1") + "\n" + data.decode("utf-16-le", "ignore")


def _signer(a):
    """Identitas penandatangan. APK palsu hasil modifikasi ulang memuat kode asli, tetapi kuncinya pasti berbeda."""
    cert = (a.get_certificates() or [None])[0]
    subject = cert.subject.human_friendly if cert else None
    return {
        "skema": [s for s, ok in (("v1", a.is_signed_v1()), ("v2", a.is_signed_v2()), ("v3", a.is_signed_v3())) if ok],
        "subjek": subject,
        "sha256": cert.sha256_fingerprint.replace(" ", "").lower() if cert else None,
        "berlaku_hingga": cert["tbs_certificate"]["validity"]["not_after"].native.date().isoformat() if cert else None,
        "debug": bool(subject) and "Android Debug" in subject,  # kunci bawaan Android Studio, bukan kunci rilis
    }


def _manifest(a, xml, full):
    """Atribut manifest yang dipakai rule di luar komponen & izin: label, flag aplikasi, prioritas receiver,
    provider terbuka, activity StrandHogg, dan host App Link yang diklaim terverifikasi."""
    app = xml.find("application")
    attr = lambda el, n: el.get(NS + n) if el is not None else None
    return {
        "label": a.get_app_name(),
        "debuggable": attr(app, "debuggable") == "true",
        "cleartext": attr(app, "usesCleartextTraffic") == "true",
        "prioritas_receiver": {full(el.get(NS + "name")): max((_int(f.get(NS + "priority")) or 0 for f in el.findall("intent-filter")), default=0)
                               for el in xml.iter("receiver")},
        "provider_terbuka": [full(el.get(NS + "name")) for el in xml.iter("provider")
                             if el.get(NS + "exported") == "true" and el.get(NS + "grantUriPermissions") == "true"],
        # StrandHogg: taskAffinity kosong + singleTask membuat activity bisa menyusup ke task aplikasi lain (login palsu)
        "hijack_task": [full(el.get(NS + "name")) for el in xml.iter("activity")
                        if el.get(NS + "taskAffinity") == "" and LAUNCH_MODE.get(el.get(NS + "launchMode"), el.get(NS + "launchMode")) == "singleTask"],
        "applink_host": sorted({d.get(NS + "host") for el in xml.iter("activity") for f in el.findall("intent-filter")
                                if f.get(NS + "autoVerify") == "true" for d in f.findall("data") if d.get(NS + "host")}),
    }


def _nsc(path):
    """res/xml yang berisi network-security-config: izin lalu lintas tanpa TLS dan kepercayaan pada CA pengguna.
    Nilai atributnya yang dibaca (bukan sekadar nama), supaya config yang justru memperketat tidak ikut tertandai."""
    out = {"cleartext": False, "user_ca": False}
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            if not (info.filename.startswith("res/xml/") and info.filename.endswith(".xml")) or info.file_size > RAW_SCAN_LIMIT:
                continue
            try:
                xml = AXMLPrinter(z.read(info)).get_xml().decode("utf-8", "ignore")
            except Exception:  # bukan AXML atau rusak: berkas lain tetap diperiksa
                continue
            if "<network-security-config" in xml:
                out["cleartext"] |= 'cleartextTrafficPermitted="true"' in xml
                out["user_ca"] |= 'src="user"' in xml
    return out


def _magic(head):
    return next((t for m, t in MAGIC.items() if head.startswith(m)), None)


def _arsip(path):
    """Isi arsip di luar manifest/DEX: pustaka native, muatan yang disamarkan sebagai gambar atau diselipkan di
    assets (pola dropper), penanda uji antivirus EICAR, dan jejak apktool (APK dibongkar lalu dirakit ulang)."""
    out = {"native": [], "payload_tersamar": [], "payload_eksekusi": [], "eicar": [], "apktool": []}
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            n = info.filename
            low = n.lower()
            if low.endswith(".so"):
                out["native"].append(n)
            if n == "apktool.yml" or n.startswith(("original/", "unknown/")):
                out["apktool"].append(n)
            if info.is_dir():
                continue
            with z.open(info) as fh:
                head = fh.read(8)
                tipe = _magic(head)
                if tipe and low.endswith(IMAGE_EXT):
                    out["payload_tersamar"].append(f"{n}: berkas gambar berisi {tipe}")
                elif tipe in ("dex", "elf") and low.startswith(("assets/", "res/raw/")):
                    out["payload_eksekusi"].append(f"{n}: {tipe}")
                if info.file_size <= EICAR_SCAN_LIMIT and EICAR in head + fh.read():
                    out["eicar"].append(n)
    return out


def parse(path):
    """Path APK yang sudah lolos validator -> dict hasil ekstraksi. Init APK/manifest diisolasi: manifest
    rusak tidak membatalkan scan, hanya menyisakan sinyal tingkat-arsip + tanda manifest_rusak (rule R24)."""
    galat = []
    try:
        a = APK(path)
        xml = a.get_android_manifest_xml()
        package = a.get_package()
    except Exception as exc:  # manifest rusak/disengaja: jangan batalkan scan, lanjut ke jalur zip-only
        a, xml, package = None, None, None
        galat.append(f"Manifest APK: {type(exc).__name__}: {exc}")
    manifest_rusak = xml is None
    if manifest_rusak and not galat:  # APK terbaca tapi manifest kosong/None tanpa melempar
        galat.append("Manifest APK: AndroidManifest.xml tidak terbaca (kosong atau rusak).")
    # manifest boleh memakai nama relatif (".Update" atau "Update"); lengkapi dengan package seperti Android
    full = lambda n: n if not n or ("." in n and not n.startswith(".")) else f"{package}{n if n.startswith('.') else '.' + n}"

    def stage(nama, fn, kosong=list):
        """Seperti MobSF: tahap yang gagal dicatat di laporan, tahap lain tetap berjalan."""
        try:
            return fn()
        except Exception as exc:
            galat.append(f"{nama}: {type(exc).__name__}: {exc}")
            return kosong()

    components = stage("Komponen manifest", lambda: [
        {
            "type": tag,
            "name": full(el.get(NS + "name")),
            "permission": el.get(NS + "permission"),
            "actions": [ac.get(NS + "name") for ac in el.iter("action")],
        }
        for tag in ("activity", "service", "receiver")
        for el in (xml.iter(tag) if xml is not None else [])
    ])

    strings = stage("Kode DEX", lambda: [s for dex in a.get_all_dex() for s in DEX(dex).get_strings()])
    texts = strings + stage("Resource & assets", lambda: list(_raw_texts(path)))
    hosts = {}
    for u in {u.rstrip(".,;)'\"") for t in texts for u in URL_RE.findall(t)}:
        try:
            host = urlsplit(u).hostname or ""
        except ValueError:  # string mirip URL yang rusak, mis. "http://[%s" dari template format; bukan URL nyata
            continue
        if "." in host:  # "https://appx" atau "https://www" adalah potongan string, bukan alamat yang bisa dihubungi
            hosts[u] = host
    urls = sorted(hosts)
    # IP hanya dari host URL atau string DEX yang isinya persis IP(:port); "1.2.0.0" di tengah teks sering nomor versi.
    # shortcut: IP tanpa port dengan oktet pertama < 10 ("1.5.1.3", "3.1.8.100") dianggap nomor versi; blok publik
    # 1.x-9.x (mis. AWS 3.x) ikut terlewat, perbaiki bila ada daftar IP pelaku nyata di rentang itu.
    candidates = list(hosts.values()) + [s.split(":")[0] for s in strings
                                         if IP_ONLY_RE.fullmatch(s) and (":" in s or int(s.split(".")[0]) >= 10)]
    ips = sorted({ip for ip in candidates if IPV4_RE.fullmatch(ip) and all(int(p) <= 255 for p in ip.split("."))})

    permissions = stage("Izin", lambda: sorted(set(a.get_permissions())))
    signer = stage("Sertifikat", lambda: _signer(a), kosong=dict)
    manifest = stage("Atribut manifest", lambda: _manifest(a, xml, full), kosong=dict)
    nsc = stage("Network security config", lambda: _nsc(path), kosong=dict)
    arsip = stage("Isi arsip", lambda: _arsip(path), kosong=dict)
    versi = stage("Versi & SDK", lambda: {
        "version_name": a.get_androidversion_name(),
        "version_code": _int(a.get_androidversion_code()),
        "min_sdk": _int(a.get_min_sdk_version()),
        "target_sdk": _int(a.get_target_sdk_version()),
    }, kosong=dict)

    return {
        "sha256": sha256_file(path),
        "package": package,
        "version_name": versi.get("version_name"),
        "version_code": versi.get("version_code"),
        "min_sdk": versi.get("min_sdk"),
        "target_sdk": versi.get("target_sdk"),
        "permissions": permissions,
        "dangerous_permissions": [p for p in permissions if p in DANGEROUS],
        "components": components,
        "texts": texts,  # untuk rule; tidak ikut ke laporan
        "urls": urls,
        "ips": ips,
        "sertifikat": signer,
        "manifest": manifest,  # untuk rule; tidak ikut ke laporan (seperti texts)
        "nsc": nsc,
        "arsip": arsip,
        "manifest_rusak": manifest_rusak,
        "galat": galat,
    }
