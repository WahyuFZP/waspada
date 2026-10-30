"""Ekstraksi statis APK dengan Androguard 4.1.4. Tidak ada yang dijalankan; hanya membaca isi arsip."""
import hashlib
import re
import zipfile
from urllib.parse import urlsplit

from loguru import logger

from androguard.core.apk import APK
from androguard.core.dex import DEX

logger.remove()  # androguard mencetak log debug sangat banyak ke stderr

NS = "{http://schemas.android.com/apk/res/android}"
URL_RE = re.compile(r"https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+")
IPV4_RE = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}")
IP_ONLY_RE = re.compile(r"(?:\d{1,3}\.){3}\d{1,3}(?::\d{1,5})?")
RAW_SCAN_LIMIT = 5 * 1024 * 1024  # resource/asset lebih besar dari ini dilewati agar scan tetap cepat

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
    """Teks dari resources.arsc & assets: tempat token/URL pelaku sering disimpan selain di DEX."""
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            if (info.filename == "resources.arsc" or info.filename.startswith("assets/")) and info.file_size <= RAW_SCAN_LIMIT:
                data = z.read(info)
                # string pool arsc bisa UTF-8 atau UTF-16
                yield data.decode("latin-1") + "\n" + data.decode("utf-16-le", "ignore")


def parse(path):
    """Path APK yang sudah lolos validator -> dict hasil ekstraksi."""
    a = APK(path)
    xml = a.get_android_manifest_xml()

    package = a.get_package()
    # manifest boleh memakai nama relatif (".Update" atau "Update"); lengkapi dengan package seperti Android
    full = lambda n: n if not n or ("." in n and not n.startswith(".")) else f"{package}{n if n.startswith('.') else '.' + n}"
    components = []
    for tag in ("activity", "service", "receiver"):
        for el in xml.iter(tag) if xml is not None else []:
            components.append({
                "type": tag,
                "name": full(el.get(NS + "name")),
                "permission": el.get(NS + "permission"),
                "actions": [ac.get(NS + "name") for ac in el.iter("action")],
            })

    strings = [s for dex in a.get_all_dex() for s in DEX(dex).get_strings()]
    texts = strings + list(_raw_texts(path))
    urls = sorted({u.rstrip(".,;)'\"") for t in texts for u in URL_RE.findall(t)})
    # IP hanya dari host URL atau string DEX yang isinya persis IP(:port); "1.2.0.0" di tengah teks sering nomor versi
    candidates = [urlsplit(u).hostname or "" for u in urls] + [s.split(":")[0] for s in strings if IP_ONLY_RE.fullmatch(s)]
    ips = sorted({ip for ip in candidates if IPV4_RE.fullmatch(ip) and all(int(p) <= 255 for p in ip.split("."))})

    permissions = sorted(set(a.get_permissions()))

    return {
        "sha256": sha256_file(path),
        "package": package,
        "version_name": a.get_androidversion_name(),
        "version_code": _int(a.get_androidversion_code()),
        "min_sdk": _int(a.get_min_sdk_version()),
        "target_sdk": _int(a.get_target_sdk_version()),
        "permissions": permissions,
        "dangerous_permissions": [p for p in permissions if p in DANGEROUS],
        "components": components,
        "texts": texts,  # untuk rule; tidak ikut ke laporan
        "urls": urls,
        "ips": ips,
    }
