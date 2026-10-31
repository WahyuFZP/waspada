"""Analisa akhir setelah rule engine: ubah laporan teknis menjadi kesimpulan yang bisa ditindaklanjuti orang awam.

Tiga pemeriksaan otomatis: (1) domain dikelompokkan menjadi milik aplikasi / layanan dikenal / lainnya,
(2) hash APK dicocokkan ke MalwareBazaar (abuse.ch) bila kunci API diatur, (3) sertifikat penandatangan.
Hanya hash yang dikirim ke luar, tidak pernah file APK-nya.
"""
import os
from collections import Counter
from urllib.parse import urlsplit

import httpx

# Domain terdaftar (eTLD+1) layanan & SDK yang wajar muncul di aplikasi sah. Bukan jaminan aman, hanya bukan "asing".
KNOWN = {
    "google.com", "googleapis.com", "gstatic.com", "android.com", "goo.gl","firebaseio.com",
    "firebase.com", "crashlytics.com", "app-measurement.com", "googlesyndication.com", "googleadservices.com",
    "doubleclick.net", "youtube.com", "facebook.com", "twitter.com", "linkedin.com", "whatsapp.com", "wa.me",
    "github.com", "mixpanel.com", "branch.io", "bnc.lt", "app.link", "onelink.me", "appsflyer.com", "adjust.com",
    "split.io", "sentry.io", "onesignal.com", "here.com", "hereapi.com", "alipay.com", "alipay.net",
    "alipayobjects.com", "alipayplus.com", "alipaydev.com", "alipay-eco.com", "marmot-cloud.com", "taobao.com",
    "alibaba.com", "uc.cn", "dbankcloud.com", "dbankcloud.cn", "dbankcloud.asia", "dbankcloud.eu", "dbankcloud.ru",
    "hicloud.com", "huawei.com", "xiaomi.com", "xiaomi.net", "live.com", "microsoft.com", "yahoo.com", "paypal.com",
    "twilio.com", "zendesk.com", "apache.org", "w3.org", "mozilla.org", "material.io", "opentelemetry.io",
    "zetetic.net", "journeyapps.com", "kotlinlang.org", "jetbrains.com", "gradle.org", "schema.org", "example.com",
}
SECOND_LEVEL = {"co", "ac", "go", "or", "web", "my", "sch", "com", "net", "org", "gov", "edu"}
MB_API = "https://mb-api.abuse.ch/api/v1/"


def registrable(host):
    """api.m.dana.id -> dana.id; www.klikbca.co.id -> klikbca.co.id (cukup untuk TLD Indonesia & umum)."""
    parts = host.lower().rstrip(".").split(".")
    n = 3 if len(parts) > 2 and len(parts[-1]) == 2 and parts[-2] in SECOND_LEVEL else 2
    return ".".join(parts[-n:])


def group_domains(urls, package):
    """-> [{domain, jumlah, kategori}] dengan kategori: aplikasi | dikenal | lainnya."""
    # id.dana -> dana.id, com.teleca.jamendo -> jamendo.com: nama merek bisa di segmen mana pun setelah TLD
    brands = {s.lower() for s in (package or "").split(".")[1:]}
    counts = Counter(registrable(urlsplit(u).hostname) for u in urls)

    def kategori(d):
        if d.split(".")[0] in brands:
            return "aplikasi"
        return "dikenal" if d in KNOWN else "lainnya"

    order = {"lainnya": 0, "aplikasi": 1, "dikenal": 2}
    rows = [{"domain": d, "jumlah": n, "kategori": kategori(d)} for d, n in counts.items()]
    return sorted(rows, key=lambda r: (order[r["kategori"]], -r["jumlah"], r["domain"]))


def lookup_hash(sha256):
    """MalwareBazaar: apakah file ini sudah dikenal sebagai malware oleh komunitas peneliti."""
    key = os.environ.get("ABUSECH_AUTH_KEY")
    if not key:
        return {"status": "dilewati", "keterangan": "Kunci API abuse.ch (ABUSECH_AUTH_KEY) belum diatur."}
    try:
        r = httpx.post(MB_API, data={"query": "get_info", "hash": sha256}, headers={"Auth-Key": key}, timeout=10)
        body = r.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {"status": "galat", "keterangan": f"MalwareBazaar tidak dapat dihubungi: {type(exc).__name__}"}
    if body.get("query_status") == "ok" and body.get("data"):
        d = body["data"][0]
        return {"status": "dikenal_malware", "keterangan": f"Tercatat di MalwareBazaar sebagai {d.get('signature') or 'malware'}.",
                "tag": d.get("tags") or [], "pertama_dilihat": d.get("first_seen")}
    if body.get("query_status") == "hash_not_found":
        return {"status": "tidak_ditemukan", "keterangan": "Belum pernah dilaporkan di MalwareBazaar."}
    return {"status": "galat", "keterangan": f"Jawaban MalwareBazaar: {body.get('query_status')}"}


RANK = ["Tidak ditemukan indikasi berbahaya", "Mencurigakan", "Berbahaya"]
SARAN = {
    "Berbahaya": [
        "Jangan pasang aplikasi ini. Bila sudah terpasang, hapus dan putuskan internet ponsel.",
        "Segera ganti PIN/kata sandi bank dan dompet digital dari perangkat lain.",
        "Hubungi bank Anda untuk memblokir transaksi mencurigakan, dan laporkan ke petugas siber satuan.",
    ],
    "Mencurigakan": [
        "Jangan pasang dulu. Unduh aplikasi hanya dari Google Play atau situs resmi penerbitnya.",
        "Tanyakan ke pengirim file, atau minta petugas siber satuan memeriksa lebih lanjut.",
    ],
    "Tidak ditemukan indikasi berbahaya": [
        "Pastikan aplikasi tetap diunduh dari sumber resmi; pemeriksaan statis tidak menjamin aman 100%.",
        "Cocokkan nama package dan penerbit dengan yang tercantum di Google Play.",
    ],
}


def conclude(parsed, packer, findings, level):
    """Gabungkan rule engine + pemeriksaan otomatis menjadi status, alasan, dan saran."""
    cert = parsed.get("sertifikat") or {}
    intel = lookup_hash(parsed["sha256"])
    domains = group_domains(parsed["urls"], parsed["package"])
    alasan, status = [], RANK[0]

    def naik(ke):  # status hanya bisa naik, tidak pernah turun
        nonlocal status
        status = max(status, ke, key=RANK.index)

    if intel["status"] == "dikenal_malware":
        naik("Berbahaya")
        alasan.append(intel["keterangan"])
    if level == "Tinggi":
        naik("Berbahaya")
    elif level == "Sedang":
        naik("Mencurigakan")
    alasan += [f"{f.judul} ({f.rule_id})." for f in findings if f.tingkat == "tinggi"]

    if not cert:
        alasan.append("Sertifikat penandatangan tidak dapat dibaca.")
    elif not cert["skema"]:
        naik("Mencurigakan")
        alasan.append("APK tidak ditandatangani; aplikasi resmi selalu ditandatangani penerbitnya.")
    elif cert["debug"]:
        naik("Mencurigakan")
        alasan.append("Ditandatangani dengan kunci debug Android Studio, bukan kunci rilis penerbit resmi.")

    asing = [d for d in domains if d["kategori"] == "lainnya"]
    if asing:
        alasan.append(f"{len(asing)} domain di luar milik aplikasi dan layanan umum; perlu ditinjau analis.")
    if packer.get("terdeteksi"):
        alasan.append("Sebagian kode disembunyikan, jadi isi sebenarnya mungkin tidak terlihat.")
    if parsed["galat"]:
        alasan.append("Sebagian tahap pemeriksaan gagal; kesimpulan ini belum lengkap.")
    if not alasan:
        alasan.append("Tidak ada aturan deteksi yang terpicu.")
    if intel["status"] == "tidak_ditemukan":
        alasan.append(intel["keterangan"])

    return {"status": status, "alasan": alasan, "saran": SARAN[status], "intel": intel, "sertifikat": cert,
            "domain": domains}
