"""Jaga agar berkas umpan target latihan (../../fixtures/app.py: DECOYS) tetap cocok dengan tanda-isi
deteksi pemeriksa (fetch._looks_exposed). Ikut dijalankan oleh `pytest` backend, sehingga drift pada
EXPOSED / _looks_exposed langsung ketahuan di sini. Lihat ../../fixtures/README.md."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "fixtures"))

from app import DECOYS  # noqa: E402  (target latihan di fixtures/, bukan FastAPI app backend)
from fetch import EXPOSED, _looks_exposed  # noqa: E402


def test_umpan_sesuai_path_probe():
    # daftar umpan harus sama persis dengan path yang diprobe scanner
    assert set(DECOYS) == set(EXPOSED)


def test_setiap_umpan_terdeteksi():
    for path, (body, ctype) in DECOYS.items():
        assert _looks_exposed(path, body[:4096], ctype), f"{path} tidak cocok tanda-isi scanner"
