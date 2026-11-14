"""Struktur Finding untuk pemeriksa keamanan web (lihat docs/web-scanner-concept.md §5)."""
from dataclasses import dataclass, field

# selaras pita CVSS; dipakai untuk mengurutkan dan menentukan postur
TINGKAT = ("info", "rendah", "sedang", "tinggi", "kritis")


@dataclass
class Finding:
    id: str
    kategori: str          # referensi OWASP, mis. "A05:2021 Security Misconfiguration"
    judul: str
    tingkat: str           # salah satu TINGKAT
    perbaikan: str
    bukti: list[str] = field(default_factory=list)
    lokasi: str = ""       # URL/endpoint tempat temuan diamati
    cwe: str = ""
    keyakinan: str = "tinggi"   # rendah | sedang | tinggi
    dampak: str = ""
    referensi: list[str] = field(default_factory=list)
    cuplikan: dict = field(default_factory=dict)  # {nginx, apache} konfigurasi siap-tempel (opsional, #7)
    edukasi: dict = field(default_factory=dict)  # kartu "Pelajari dulu" {apa, kenapa, dampak} (opsional, #8)
