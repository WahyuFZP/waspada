import hashlib

import packer
from parser import parse


def test_parses_manifest_of_real_apk(benign_apk):
    path = benign_apk("com.politedroid_4.apk")
    p = parse(path)
    assert p["sha256"] == hashlib.sha256(open(path, "rb").read()).hexdigest()
    assert (p["package"], p["version_name"], p["version_code"]) == ("com.politedroid", "1.3", 4)
    assert (p["min_sdk"], p["target_sdk"]) == (3, None)  # target SDK tidak dicantumkan: None, bukan error
    assert p["permissions"] == ["android.permission.READ_CALENDAR", "android.permission.RECEIVE_BOOT_COMPLETED"]
    assert {"type": "receiver", "name": "com.politedroid.Update", "permission": None,
            "actions": ["android.intent.action.BOOT_COMPLETED"]} in p["components"]


def test_extracts_urls_and_services(benign_apk):
    p = parse(benign_apk("com.teleca.jamendo_35.apk"))
    assert "http://api.jamendo.com/get2/" in p["urls"]
    # nama relatif di manifest (".service.PlayerService") dilengkapi dengan package
    assert [c["name"] for c in p["components"] if c["type"] == "service"] == [
        "com.teleca.jamendo.service.PlayerService", "com.teleca.jamendo.service.DownloadService"]
    assert p["ips"] == []
    # INTERNET & WAKE_LOCK adalah izin normal; hanya izin dari daftar berisiko yang ditandai
    assert p["dangerous_permissions"] == ["android.permission.READ_PHONE_STATE", "android.permission.WRITE_EXTERNAL_STORAGE"]


def test_apkid_compiler_marker_is_not_a_packer(benign_apk):
    pk = packer.scan(benign_apk("com.politedroid_4.apk"))
    assert pk["terdeteksi"] is False and "galat" not in pk
    assert "r8 without marker (suspicious)" in pk["info_lain"]["compiler"]


def test_malformed_url_string_is_skipped(benign_apk, monkeypatch):
    # "http://[" membuat urlsplit melempar ValueError (Invalid IPv6 URL); dulu menggagalkan seluruh analisis
    import parser as parser_mod
    monkeypatch.setattr(parser_mod, "_raw_texts", lambda _: ["http://[%s:8080/x", "https://ok.example.org/a"])
    p = parse(benign_apk("com.politedroid_4.apk"))
    assert "https://ok.example.org/a" in p["urls"]
    assert not any("[" in u for u in p["urls"])


def test_failed_stage_is_reported_not_fatal(benign_apk, monkeypatch):
    import parser as parser_mod

    def boom(_):
        raise OSError("arsip rusak")
        yield

    monkeypatch.setattr(parser_mod, "_raw_texts", boom)
    p = parse(benign_apk("com.politedroid_4.apk"))
    assert p["package"] == "com.politedroid"  # manifest tetap terbaca
    assert p["galat"] == ["Resource & assets: OSError: arsip rusak"]
