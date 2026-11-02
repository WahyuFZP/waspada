"""Rule engine MVP (PRD v1.2 §7). Setiap rule hanya menghasilkan Finding bila terpicu, lengkap dengan bukti."""
import ipaddress
import re
from collections import Counter
from urllib.parse import urlsplit

from models import Finding

P = "android.permission."
SMS_RECEIVED = "android.provider.Telephony.SMS_RECEIVED"
# token bisa menempel langsung setelah "/bot" (tanpa batas kata), jadi URL + token ditangkap sebagai satu bukti
TELEGRAM_RE = re.compile(r"api\.telegram\.org/bot(?:\d{8,10}:[A-Za-z0-9_-]{35})?|(?<![\w:])\d{8,10}:[A-Za-z0-9_-]{35}(?![\w-])")
TOKEN_RE = re.compile(r"(\d{8,10}):([A-Za-z0-9_-]{35})")

# Konfigurasi R09: domain umum yang wajar muncul di APK sah, dan layanan pemendek tautan
EXCLUDED_DOMAINS = (
    "android.com", "google.com", "googleapis.com", "gstatic.com", "googlesyndication.com", "doubleclick.net",
    "firebaseio.com", "firebase.com", "crashlytics.com", "facebook.com", "w3.org", "apache.org", "xml.org",
    "github.com", "gradle.org", "jetbrains.com", "kotlinlang.org", "mozilla.org", "example.com", "schema.org",
)
SHORTENERS = ("bit.ly", "s.id", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly", "shorturl.at", "rb.gy", "ow.ly",
              "short.gy", "rebrand.ly")

# R12: istilah khas taruhan. "bank", "deposit", "bonus" saja tidak cukup karena juga ada di aplikasi bank sah,
# jadi butuh >= 2 istilah taruhan berbeda DAN alur uang (setor/tarik)
GAMBLING_RE = re.compile(r"\b(casino|kasino|togel|lottery|lotre|sabung|poker|baccarat|roulette|jackpot|maxwin|gacor|"
                         r"sportsbook|slot online|turnover)\b", re.I)
MONEY_RE = re.compile(r"\b(deposit|withdraw|withdrawal|tarik dana|setor)\b", re.I)
# R13: baris KEY=VALUE berisi rahasia di file konfigurasi yang ikut dibungkus (.env, *.properties); hanya nama kunci
# yang dilaporkan, nilainya tidak pernah ditampilkan
SECRET_LINE_RE = re.compile(r"(?m)^\s*([A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|API_KEY|PRIVATE_KEY|SALT|AUTH)[A-Z0-9_]*)"
                            r"\s*=\s*['\"]?(?!null\b)[^'\"\n]{8,}")
# R14: kategori APKiD yang berarti aplikasi berusaha mendeteksi atau mengecoh alat analisis
EVASION = ("anti_vm", "anti_debug", "anti_disassembly", "manipulator")


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


def evaluate(p, packer):
    """p = hasil parser.parse(); packer = hasil packer.scan(). -> list[Finding]"""
    perms = set(p["permissions"])
    found = []

    def hit(*args, **kw):
        found.append(Finding(*args, **kw))

    sms = sorted(perms & {P + "READ_SMS", P + "RECEIVE_SMS"})
    if sms:
        receivers = [f"receiver {c['name']}: {SMS_RECEIVED}" for c in p["components"]
                     if c["type"] == "receiver" and SMS_RECEIVED in c["actions"]]
        hit("R01", "Aplikasi dapat membaca SMS", "tinggi", 20, sms + receivers,
            "Izin SMS sering dipakai untuk mencuri kode OTP bank atau WhatsApp yang dikirim lewat SMS.")

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

    bets = Counter(m.group(0).lower() for t in p["texts"] for m in GAMBLING_RE.finditer(t))
    money = Counter(m.group(0).lower() for t in p["texts"] for m in MONEY_RE.finditer(t))
    if len(bets) >= 2 and money:
        hit("R12", "Aplikasi judi online", "tinggi", 30,
            [f"{k} ×{n}" for k, n in bets.most_common()] + [f"{k} ×{n}" for k, n in money.most_common()],
            "Memuat istilah taruhan (kasino, togel, sabung, dst.) sekaligus alur setor dan tarik dana. Judi online "
            "dilarang hukum Indonesia, dan data rekening yang dimasukkan diserahkan ke operator ilegal.")

    secrets = sorted({m.group(1) for t in p["texts"] for m in SECRET_LINE_RE.finditer(t)})
    if secrets:
        hit("R13", "Kunci rahasia server tertanam di aplikasi", "sedang", 10, secrets,
            "Aplikasi membawa file konfigurasi berisi token atau kunci layanan. Aplikasi resmi tidak menyimpan rahasia "
            "seperti ini di dalam APK. Yang dilaporkan hanya nama kuncinya; nilainya tidak ditampilkan dan tidak "
            "pernah dipakai.")

    evasive = [f"{k}: {v}" for k in EVASION for v in packer.get("info_lain", {}).get(k, [])]
    if evasive:
        hit("R14", "Berusaha menghindari pemeriksaan", "sedang", 10, evasive,
            "Aplikasi memeriksa apakah sedang berjalan di emulator atau dianalisis, agar perilaku aslinya tersembunyi "
            "dari peneliti. Aplikasi bank sah kadang juga melakukannya, jadi ini ciri pendukung, bukan bukti tunggal.")

    combo = [f.rule_id for f in found if f.rule_id in {"R01", "R02", "R03", "R04", "R10"}]
    if len(combo) >= 2:
        hit("R07", "Kombinasi ciri banking trojan", "tinggi", 25, combo,
            "Masing-masing izin bisa wajar, tetapi gabungannya cocok dengan pola aplikasi pencuri OTP dan data "
            "perbankan.")

    return sorted(found, key=lambda f: f.rule_id)
