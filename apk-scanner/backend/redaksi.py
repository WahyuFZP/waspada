"""Redaksi terpusat (#11): samarkan rahasia di dalam string bukti/URL sebelum disimpan & diunduh,
sehingga laporan keamanan sendiri tidak membocorkan rahasia saat dibagikan. Nilai asli TIDAK pernah
disimpan — cukup konteks + 4 karakter awal agar pemilik tetap bisa menindaklanjuti. Jangan over-masking."""
import re

# key=value / key: value yang namanya menandakan rahasia -> samarkan NILAI-nya (nama & struktur tetap)
_SECRET_KEY = re.compile(
    r"(?i)\b(sessionid|jsessionid|phpsessid|sid|token|access[_-]?token|refresh[_-]?token|secret|"
    r"client[_-]?secret|password|passwd|pwd|api[_-]?key|apikey|auth|authorization|signature|sig)\b"
    r"(\s*[=:]\s*)([^\s;&\"'<>]{4,})")
_TELEGRAM = re.compile(r"\b(\d{8,10}):[A-Za-z0-9_-]{35}\b")
_EMAIL = re.compile(r"([\w.+-]{1,2})[\w.+-]*(@[\w-]+\.[\w.-]+)")
_PHONE = re.compile(r"(?<!\d)((?:\+?62|0)8\d{2})\d{5,11}(?!\d)")


def _potong(v):
    return (v[:4] + "…") if len(v) > 4 else "…"


def redaksi(text):
    """Samarkan rahasia pada satu string. Non-string dikembalikan apa adanya."""
    if not isinstance(text, str):
        return text
    text = _SECRET_KEY.sub(lambda m: m.group(1) + m.group(2) + _potong(m.group(3)), text)
    text = _TELEGRAM.sub(lambda m: m.group(1) + ":…", text)
    text = _EMAIL.sub(lambda m: m.group(1) + "…" + m.group(2), text)
    text = _PHONE.sub(lambda m: m.group(1) + "…", text)
    return text
