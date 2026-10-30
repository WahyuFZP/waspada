import zipfile

import pytest

import validator
from validator import InvalidApk, validate


def _zip(tmp_path, names):
    path = tmp_path / "x.apk"
    with zipfile.ZipFile(path, "w") as z:
        for n in names:
            z.writestr(n, b"isi")
    return str(path)


def test_rejects_non_zip(tmp_path):
    p = tmp_path / "catatan.txt"
    p.write_text("bukan apk")
    with pytest.raises(InvalidApk, match="bukan file APK"):
        validate(str(p), p.stat().st_size)


def test_rejects_zip_without_manifest_or_dex(tmp_path):
    with pytest.raises(InvalidApk, match="AndroidManifest"):
        validate(_zip(tmp_path, ["classes.dex"]), 10)
    with pytest.raises(InvalidApk, match="classes.dex"):
        validate(_zip(tmp_path, ["AndroidManifest.xml"]), 10)


def test_rejects_oversize_and_zip_bomb(tmp_path, monkeypatch):
    with pytest.raises(InvalidApk, match="150 MB"):
        validate(_zip(tmp_path, ["AndroidManifest.xml", "classes.dex"]), validator.MAX_BYTES + 1)
    monkeypatch.setattr(validator, "MAX_UNCOMPRESSED", 4)  # isi 2 file x 3 byte > 4 byte
    with pytest.raises(InvalidApk, match="zip bomb"):
        validate(_zip(tmp_path, ["AndroidManifest.xml", "classes.dex"]), 10)


def test_accepts_real_apk(benign_apk):
    path = benign_apk("com.politedroid_4.apk")
    validate(path, 1)  # tidak melempar
