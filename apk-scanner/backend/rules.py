"""Rule engine MVP (PRD v1.1 §7). Setiap rule hanya menghasilkan Finding bila terpicu, lengkap dengan bukti."""
import ipaddress
import re
import unicodedata
from urllib.parse import urlsplit

from models import Finding

P = "android.permission."
SMS_RECEIVED = "android.provider.Telephony.SMS_RECEIVED"
BOOT_COMPLETED = "android.intent.action.BOOT_COMPLETED"
FCM_EVENT = "com.google.firebase.MESSAGING_EVENT"
# R13: package resmi -> nama merek yang sering ditiru APK "update" palsu. Dirawat manual; entri yang keliru hanya
# berarti tidak cocok (tidak menimbulkan false positive). Sidik jari penerbit resmi ditunda ke v2 (PRD §2).
BRAND_PACKAGES = {
    "id.co.bri.brimo": "BRImo", "com.bca": "BCA mobile", "id.bmri.livin": "Livin' by Mandiri",
    "src.com.bni": "BNI Mobile Banking", "com.bsm.activity2": "BSI Mobile", "id.co.cimbniaga.mobile.android": "OCTO Mobile",
    "com.btpn.dc": "Jenius", "com.jago.digitalBanking": "Jago", "id.dana": "DANA", "ovo.id": "OVO",
    "com.gojek.app": "Gojek", "com.shopee.id": "Shopee", "com.telkom.mwallet": "LinkAja",
    "com.tokopedia.tkpd": "Tokopedia", "com.whatsapp": "WhatsApp", "org.telegram.messenger": "Telegram",
}
BRAND_TOKENS = {re.sub(r"[^a-z0-9]", "", nama.split()[0].lower()): pkg for pkg, nama in BRAND_PACKAGES.items()}
# Huruf Cyrillic/Yunani yang tampak sama dengan Latin, dipetakan balik agar label "ВRImo" terbaca "BRImo"
CONFUSABLE = str.maketrans(
    "АВЕКМНОРСТХаеорсухіѕј"
    "ΑΒΕΖΗΙΚΜΝΟΡΤΥΧον",
    "ABEKMHOPCTXaeopcyxisj" "ABEZHIKMNOPTYXov")
UNVERIFIABLE_TLD = (".test", ".local", ".invalid", ".example")  # Digital Asset Links tidak mungkin terverifikasi
# R20: string anti-analisis, dicocokkan persis dengan string DEX (bukan substring) agar kata umum tidak ikut
ANTI_ANALISIS = {
    "root": ("/system/bin/su", "/system/xbin/su", "/sbin/su", "eu.chainfire.supersu", "com.topjohnwu.magisk"),
    "emulator": ("generic", "goldfish", "ranchu", "sdk_gphone", "google_sdk", "genymotion", "vbox86", "nox"),
    "instrumentasi": ("frida-server", "frida", "LIBFRIDA", "xposed", "de.robv.android.xposed.XposedBridge"),
    "debugger": ("isDebuggerConnected",),
}
DEVICE_ID = ("android_id", "getDeviceId", "getImei", "getSubscriberId", "getSimSerialNumber")
# token bisa menempel langsung setelah "/bot" (tanpa batas kata), jadi URL + token ditangkap sebagai satu bukti
TELEGRAM_RE = re.compile(r"api\.telegram\.org/bot(?:\d{8,10}:[A-Za-z0-9_-]{35})?|(?<![\w:])\d{8,10}:[A-Za-z0-9_-]{35}(?![\w-])")
TOKEN_RE = re.compile(r"(\d{8,10}):([A-Za-z0-9_-]{35})")

# Konfigurasi R09: domain umum yang wajar muncul di APK sah, dan layanan pemendek tautan
EXCLUDED_DOMAINS = (
    "android.com", "google.com", "googleapis.com", "gstatic.com", "googlesyndication.com", "doubleclick.net",
    "firebaseio.com", "firebase.com", "crashlytics.com", "facebook.com", "w3.org", "apache.org", "xml.org",
    "github.com", "gradle.org", "jetbrains.com", "kotlinlang.org", "mozilla.org", "example.com", "schema.org",
)
SHORTENERS = ("bit.ly", "s.id", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly", "shorturl.at", "rb.gy", "ow.ly")


def mask_token(text):
    """123456789:AAE…xyz agar token pelaku tidak tersebar ulang lewat laporan."""
    return TOKEN_RE.sub(lambda m: f"{m[1]}:{m[2][:3]}…{m[2][-3:]}", text)


def _host(url):
    return (urlsplit(url).hostname or "").lower()


def _matches_domain(host, domains):
    return any(host == d or host.endswith("." + d) for d in domains)


def _components(p, kind, permission, action):
    """Komponen yang dilindungi `android:permission` tertentu atau punya intent filter action tertentu."""
    return [f"{c['type']} {c['name']}: " + (c["permission"] if c["permission"] == permission else action)
            for c in p["components"]
            if c["type"] == kind and (c["permission"] == permission or action in c["actions"])]


def _label_tokens(label):
    """'ВRImo' -> {'brimo'}: huruf serupa dipetakan ke Latin, lalu dipecah per kata (cocok utuh, bukan substring)."""
    return set(re.split(r"[^a-z0-9]+", unicodedata.normalize("NFKC", label or "").translate(CONFUSABLE).lower())) - {""}


def _mixed_script(label):
    """Satu kata memuat huruf Latin dan huruf aksara lain (homoglyph); label yang seluruhnya non-Latin tidak dihitung."""
    return any(any("a" <= c.lower() <= "z" for c in w) and any(c.isalpha() and ord(c) > 0x024F for c in w)
               for w in (label or "").split())


def evaluate(p, packer):
    """p = hasil parser.parse(); packer = hasil packer.scan(). -> list[Finding]"""
    perms = set(p["permissions"])
    man = p.get("manifest") or {}  # atribut manifest tambahan; kosong pada data uji lama (semua rule baru memakai .get)
    found = []

    def hit(*args, **kw):
        found.append(Finding(*args, **kw))

    sms = sorted(perms & {P + "READ_SMS", P + "RECEIVE_SMS"})
    sms_receivers = [c["name"] for c in p["components"] if c["type"] == "receiver" and SMS_RECEIVED in c["actions"]]
    if sms:
        receivers = [f"receiver {n}: {SMS_RECEIVED}" for n in sms_receivers]
        # receiver SMS_RECEIVED adalah bukti lebih kuat daripada izin saja (catatan PRD v1.1 §7 R01): +10
        hit("R01", "Aplikasi dapat membaca SMS", "tinggi", 30 if receivers else 20, sms + receivers,
            "Izin SMS sering dipakai untuk mencuri kode OTP bank atau WhatsApp yang dikirim lewat SMS.")

    # R12: bentuk pencegat OTP. Izin SMS + receiver saja masih wajar (cadangan SMS); >=2 pemberat adalah pola pencuri.
    if sms and sms_receivers:
        prio = max((man.get("prioritas_receiver", {}).get(n, 0) for n in sms_receivers), default=0)
        boot = [c["name"] for c in p["components"] if c["type"] == "receiver" and BOOT_COMPLETED in c["actions"]]
        pemberat = ([f"receiver SMS_RECEIVED prioritas {prio} (mendahului aplikasi SMS bawaan)"] if prio > 0 else []) \
            + ([P + "SEND_SMS"] if P + "SEND_SMS" in perms else []) \
            + ([f"receiver {boot[0]}: {BOOT_COMPLETED} (aktif lagi setelah restart)"] if boot else []) \
            + ([P + "READ_PHONE_STATE"] if P + "READ_PHONE_STATE" in perms else [])
        if len(pemberat) >= 2:
            hit("R12", "Pola pencegat OTP lewat SMS", "tinggi", 25, pemberat,
                "Receiver SMS berprioritas tinggi, izin kirim SMS, dan aktif otomatis setelah restart adalah bentuk khas "
                "aplikasi pencegat kode OTP, bukan aplikasi cadangan SMS biasa.")

    acc = _components(p, "service", P + "BIND_ACCESSIBILITY_SERVICE", "android.accessibilityservice.AccessibilityService")
    if acc:
        hit("R02", "Memakai layanan Aksesibilitas", "tinggi", 20, acc,
            "Aksesibilitas memungkinkan aplikasi membaca isi layar dan menekan tombol atas nama Anda, "
            "termasuk di aplikasi bank.")

    if P + "SYSTEM_ALERT_WINDOW" in perms:
        hit("R03", "Dapat menampilkan layar di atas aplikasi lain", "sedang", 15, [P + "SYSTEM_ALERT_WINDOW"],
            "Dipakai untuk menampilkan halaman login palsu di atas aplikasi bank asli.")

    notif = _components(p, "service", P + "BIND_NOTIFICATION_LISTENER_SERVICE",
                        "android.service.notification.NotificationListenerService")
    if notif:
        hit("R04", "Dapat membaca semua notifikasi", "sedang", 15, notif,
            "Kode OTP yang muncul di notifikasi bisa dibaca dan diteruskan.")

    admin = _components(p, "receiver", P + "BIND_DEVICE_ADMIN", "android.app.action.DEVICE_ADMIN_ENABLED")
    if admin:
        hit("R05", "Meminta hak admin perangkat", "sedang", 15, admin,
            "Hak admin perangkat membuat aplikasi sulit dihapus dan dapat mengunci layar.")

    if P + "REQUEST_INSTALL_PACKAGES" in perms:
        hit("R06", "Dapat memasang aplikasi lain", "sedang", 10, [P + "REQUEST_INSTALL_PACKAGES"],
            "Pola 'dropper': aplikasi pertama tampak biasa, lalu memasang aplikasi berbahaya berikutnya.")

    if packer.get("terdeteksi"):
        hit("R08", "Kode disembunyikan (packer/obfuscator)", "sedang", 15, packer["detail"],
            "Kode sengaja dibungkus atau diacak sehingga sulit diperiksa. Isi sebenarnya mungkin tidak terlihat oleh "
            "pemeriksaan statis ini.")

    public_ips = [ip for ip in p["ips"] if ipaddress.ip_address(ip).is_global]
    short = [u for u in p["urls"] if _matches_domain(_host(u), SHORTENERS) and not _matches_domain(_host(u), EXCLUDED_DOMAINS)]
    if public_ips or short:
        hit("R09", "Alamat IP atau tautan pendek tertanam", "rendah", 10, public_ips + short,
            "Server yang ditulis sebagai alamat IP mentah atau disembunyikan di balik tautan pendek sering dipakai "
            "untuk menampung data curian.")

    send_api = sorted({s for s in ("sendTextMessage", "sendMultipartTextMessage") if s in p["texts"]})
    if P + "SEND_SMS" in perms and send_api:
        hit("R10", "Dapat mengirim SMS tanpa sepengetahuan Anda", "tinggi", 20, [P + "SEND_SMS"] + send_api,
            "Dipakai untuk mengirim SMS dari nomor Anda, misalnya menyebarkan tautan penipuan atau memancing OTP.")

    telegram = sorted({mask_token(m.group(0)) for t in p["texts"] for m in TELEGRAM_RE.finditer(t)})
    if telegram:
        hit("R11", "Mengirim data ke bot Telegram", "tinggi", 30, telegram,
            "Pola paling umum pencuri OTP di Indonesia: SMS dan data korban diteruskan ke bot Telegram milik pelaku. "
            "Token disamarkan di laporan dan tidak pernah dipakai untuk mengakses bot.")

    # R13: meniru aplikasi resmi. Nama package saja tidak bisa membedakan app asli dari tiruan (sidik jari resmi
    # ditunda ke v2), jadi yang dinilai: package menumpang nama resmi, package resmi berkunci debug/tanpa tanda
    # tangan, label homoglyph, atau label menyebut merek yang bukan miliknya. Versi janggal & App Link palsu menguatkan.
    pkg, label, cert = p.get("package") or "", man.get("label") or "", p.get("sertifikat") or {}
    official = next((o for o in BRAND_PACKAGES if pkg == o or pkg.startswith(o + ".")), None)
    disebut = next((BRAND_TOKENS[t] for t in _label_tokens(label) if t in BRAND_TOKENS), None)
    tiru, bobot = [], 0
    if official and pkg != official:
        tiru.append(f"package {pkg} menumpang nama resmi {official} ({BRAND_PACKAGES[official]})")
        bobot += 30
    elif official and (cert.get("debug") or (cert and not cert.get("skema"))):
        tiru.append(f"package resmi {BRAND_PACKAGES[official]} tetapi berkunci debug / tanpa tanda tangan")
        bobot += 30
    if _mixed_script(label):
        tiru.append(f"label '{label}' mencampur huruf Latin dengan aksara lain (homoglyph)")
        bobot += 20
    if disebut and pkg != disebut:
        tiru.append(f"label menyebut {BRAND_PACKAGES[disebut]} tetapi package bukan {disebut}")
        bobot += 20
    if tiru:  # penguat hanya dihitung bila sudah ada tanda peniruan
        vn = p.get("version_name") or ""
        if vn.startswith("99") or vn.count("9") >= 3:
            tiru.append(f"versionName {vn} tidak wajar")
            bobot += 10
        palsu = [h for h in man.get("applink_host", []) if h.endswith(UNVERIFIABLE_TLD)]
        if palsu:
            tiru.append(f"App Link autoVerify ke host yang tidak bisa diverifikasi: {', '.join(palsu)}")
            bobot += 10
        hit("R13", "Meniru aplikasi resmi", "tinggi" if bobot >= 30 else "sedang", min(bobot, 60), tiru,
            "Nama package, label, atau tanda tangan tidak cocok dengan aplikasi resmi yang ditirunya: pola 'update "
            "BRImo/DANA' palsu yang disebar lewat WhatsApp. Cocokkan penerbit dengan yang tercantum di Google Play.")

    # R14-R16: isi arsip. Muatan yang disamarkan sebagai gambar / diselipkan di assets (dropper), EICAR, jejak apktool.
    ar = p.get("arsip") or {}
    muatan = ar.get("payload_tersamar", []) + ar.get("payload_eksekusi", [])
    if muatan:
        hit("R14", "Muatan tersembunyi di dalam aset", "tinggi",
            min(40, 25 * bool(ar.get("payload_tersamar")) + 15 * bool(ar.get("payload_eksekusi"))), muatan,
            "Berkas yang mengaku gambar tetapi berisi ZIP/DEX/ELF, atau kode DEX/native yang diselipkan di assets, "
            "adalah muatan tahap kedua: dipasang atau dimuat setelah aplikasi pertama dipercaya pengguna.")
    if ar.get("eicar"):
        hit("R15", "Mengandung penanda uji antivirus (EICAR)", "tinggi", 30, ar["eicar"],
            "String EICAR adalah penanda standar untuk menguji antivirus; aplikasi sah tidak pernah memuatnya.")
    if ar.get("apktool"):
        hit("R16", "Jejak apktool: APK dibongkar lalu dirakit ulang", "sedang", 10, ar["apktool"],
            "Sisa berkas apktool menandakan APK ini hasil modifikasi dari APK lain: pola 'aplikasi palsu' yang "
            "dibuat dari aplikasi resmi yang dibongkar.")

    # R17: WebView tidak aman. Jembatan JS atau abai galat sertifikat saja = rendah; keduanya = wrapper phishing.
    t = set(p["texts"])
    bridge = "addJavascriptInterface" in t
    abai_tls = "onReceivedSslError" in t and "proceed" in t  # override tanpa proceed() (mis. cancel) justru aman
    akses = sorted({s for s in ("setAllowFileAccess", "setAllowUniversalAccessFromFileURLs") if s in t})
    if bridge or abai_tls:
        wv = (["addJavascriptInterface (jembatan JavaScript -> kode aplikasi)"] if bridge else []) \
            + (["onReceivedSslError + proceed (galat sertifikat TLS diabaikan)"] if abai_tls else []) + akses
        hit("R17", "WebView tidak aman", "tinggi" if bridge and abai_tls else "sedang",
            20 * bridge + 20 * abai_tls + (10 if akses else 0) + (10 if bridge and abai_tls else 0), wv,
            "Halaman login palsu dimuat di WebView: JavaScript halaman bisa memanggil kode aplikasi, dan sertifikat "
            "TLS palsu diterima tanpa peringatan, sehingga data yang diketik bisa dibaca aplikasi.")

    # R18: konfigurasi jaringan. Nilai config yang dibaca (bukan nama atributnya), jadi config pengetat tidak tertandai.
    nsc = p.get("nsc") or {}
    jaringan = (['android:usesCleartextTraffic="true"'] if man.get("cleartext") else []) \
        + (['network_security_config: cleartextTrafficPermitted="true"'] if nsc.get("cleartext") else []) \
        + (["network_security_config: mempercayai sertifikat CA yang dipasang pengguna"] if nsc.get("user_ca") else [])
    if jaringan:
        hit("R18", "Lalu lintas jaringan tidak aman", "sedang", min(30, 15 * len(jaringan)), jaringan,
            "Data boleh dikirim tanpa enkripsi atau lewat sertifikat yang dipasang pihak lain, sehingga mudah "
            "disadap atau dialihkan ke server pelaku.")

    # R19: higiene manifest. Dibatasi 30: aplikasi sah yang ceroboh bisa punya ini, jadi tidak boleh 'Tinggi' sendirian.
    higiene = (['android:debuggable="true"'] if man.get("debuggable") else []) \
        + [f"provider {n}: exported + grantUriPermissions" for n in man.get("provider_terbuka", [])] \
        + [f"activity {n}: taskAffinity kosong + singleTask (StrandHogg)" for n in man.get("hijack_task", [])]
    if higiene:
        hit("R19", "Konfigurasi manifest lemah", "sedang",
            min(30, 10 * bool(man.get("debuggable")) + 10 * bool(man.get("provider_terbuka")) + 15 * bool(man.get("hijack_task"))),
            higiene, "Mode debug, provider terbuka, atau activity yang bisa menyusup ke task aplikasi lain (StrandHogg) "
                     "mempermudah pencurian data dan tampilan login palsu.")

    # R20: anti-analisis. Aplikasi bank sah juga memeriksa root/debugger, jadi dibatasi 30 (Sedang), bukan Tinggi.
    anti = {k: v for k, v in ((k, sorted(set(v) & t)) for k, v in ANTI_ANALISIS.items()) if v}
    if anti:
        hit("R20", "Mendeteksi emulator, root, atau alat analisis", "sedang", min(30, 10 * len(anti)),
            [f"{k}: {', '.join(v)}" for k, v in anti.items()],
            "Pemeriksaan emulator/root/Frida/debugger dipakai malware untuk berhenti saat sedang dianalisis; "
            "aplikasi sah memakainya untuk perlindungan, jadi ini sinyal pendukung, bukan vonis.")

    # R21-R23: kapabilitas yang lazim di aplikasi sah (Flutter, Firebase, analitik). Dipilih sensitivitas (PRD v1.3):
    # masing-masing 30 = Sedang sendirian, dan menumpuk, sehingga aplikasi Flutter + Firebase + analitik mencapai Tinggi.
    # Bila false positive terasa: turunkan ke 0 (hanya informasi) atau batasi jumlah ketiganya di scoring.py.
    if ar.get("native"):
        hit("R21", "Memuat pustaka native (.so)", "sedang", 30, ar["native"][:10],
            "Kode native tidak terlihat oleh pemeriksaan DEX, jadi perilaku sebenarnya bisa tersembunyi di sini. "
            "Wajar di aplikasi Flutter/game; periksa bersama temuan lain.")
    fcm = [c["name"] for c in p["components"] if c["type"] == "service" and FCM_EVENT in c["actions"]]
    if fcm:
        hit("R22", "Menerima pesan push Firebase (FCM)", "sedang", 30, fcm,
            "Kanal push bisa dipakai pelaku untuk mengirim perintah ke aplikasi setelah terpasang (C2), meski juga "
            "dipakai hampir semua aplikasi sah.")
    ident = sorted(set(DEVICE_ID) & t)
    if ident:
        hit("R23", "Membaca identitas perangkat", "sedang", 30, ident,
            "ANDROID_ID/IMEI dipakai untuk mengenali korban di server pelaku, tetapi juga oleh analitik aplikasi sah.")

    combo = [f.rule_id for f in found if f.rule_id in {"R01", "R02", "R03", "R04", "R10", "R12"}]
    if len(combo) >= 2:
        hit("R07", "Kombinasi ciri banking trojan", "tinggi", 25, combo,
            "Masing-masing izin bisa wajar, tetapi gabungannya cocok dengan pola aplikasi pencuri OTP dan data "
            "perbankan.")

    return sorted(found, key=lambda f: f.rule_id)
