"""Draf laporan responsible-disclosure yang SANTUN & faktual (#18).

Hanya MENYUSUN TEKS untuk ditinjau & dikirim MANUAL oleh pelapor ke kanal resmi (lihat kepatuhan.py).
WASPADA tidak pernah mengirim apa pun. Pemicu niche: dipanggil hanya saat kasus sudah dinilai
layak-lapor (status Berbahaya atau indikasi peniru) di report.build. Bahasa sengaja di-hedge
("dugaan", "indikasi statik, bukan vonis final") agar faktual dan tidak menuduh berlebihan.
"""
from kepatuhan import PENIRU_RULES

HEDGE = "indikasi pemeriksaan statik pasif, bukan vonis final"


def _penandatangan(cert):
    if not cert:
        return "tidak dapat dibaca"
    if not cert.get("skema"):
        return "tidak ditandatangani (aplikasi resmi selalu ditandatangani penerbitnya)"
    if cert.get("debug"):
        return "kunci debug Android Studio, bukan kunci rilis penerbit resmi"
    return cert.get("subjek") or "ditandatangani (subjek tidak terbaca)"


def draf(filename, parsed, akhir, findings):
    """-> {subjek, badan, catatan}. Hanya indikator teknis (bukan bukti mentah yang mungkin berisi rahasia)."""
    pkg = parsed["package"] or "(tidak terbaca)"
    sha = parsed["sha256"]
    perms = [p.replace("android.permission.", "") for p in parsed["dangerous_permissions"]]
    tinggi = [f.judul for f in findings if f.tingkat == "tinggi"]
    peniru = any(f.rule_id in PENIRU_RULES for f in findings)
    asing = [d["domain"] for d in akhir.get("domain", []) if d["kategori"] == "lainnya"]
    intel = akhir.get("intel") or {}

    baris = [
        f"- Nama berkas   : {filename}",
        f"- Package       : {pkg}",
        f"- SHA-256       : {sha}",
        f"- Penandatangan : {_penandatangan(akhir.get('sertifikat'))}",
        f"- Status periksa: {akhir['status']} ({HEDGE})",
    ]
    if perms:
        baris.append(f"- Izin berisiko : {', '.join(perms)}")
    if tinggi:
        baris.append(f"- Indikator kuat: {'; '.join(tinggi)}")
    if asing:
        baris.append(f"- Domain di luar merek aplikasi: {', '.join(asing[:8])}")
    if intel.get("status") == "dikenal_malware":
        baris.append(f"- Intel komunitas: {intel.get('keterangan', '')}")

    pembuka = ("Melalui pemeriksaan keamanan statik pasif, sebuah berkas aplikasi Android "
               "terindikasi berpotensi berbahaya")
    if peniru:
        pembuka += " dan tampak menyamar sebagai aplikasi/merek resmi"
    pembuka += ". Kami sampaikan indikator teknis berikut untuk ditinjau pihak yang berwenang:"

    badan = "\n".join([
        "Kepada Yth. tim yang berwenang,", "",
        pembuka, "",
        *baris, "",
        ("Mohon berkenan meninjau dan menindaklanjuti sesuai kewenangan — verifikasi, peringatan "
         "kepada pengguna, atau penurunan dari toko aplikasi. Kami bersedia memberikan berkas "
         "pendukung bila diperlukan."), "",
        "Hormat kami,", "[nama & kontak pelapor]",
    ])
    # subjek ikut gate peniru agar tidak menuding peniruan di judul saat badan tak mendukungnya
    subjek = f"Dugaan aplikasi Android {'berbahaya/menyamar' if peniru else 'berbahaya'} — {pkg} ({sha[:12]})"
    catatan = ("DRAF otomatis untuk Anda TINJAU dan kirim SENDIRI ke kanal resmi — WASPADA tidak "
               "mengirim apa pun secara otomatis. Isinya indikasi static-analysis, bukan vonis final: "
               "verifikasi fakta, isi identitas pelapor, dan hapus detail yang tak perlu sebelum "
               "mengirim. Bukan nasihat hukum.")
    return {"subjek": subjek, "badan": badan, "catatan": catatan}
