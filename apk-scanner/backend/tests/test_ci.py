"""Tes transformasi gerbang CI (#9) apk: SARIF, baseline, exit-code. Tanpa jaringan/APK."""
from ci import exit_code, sarif, temuan_baru

F1 = {"rule_id": "R11", "judul": "Mengirim data ke bot Telegram", "tingkat": "tinggi", "bobot": 30, "bukti": ["api.telegram.org/..."]}
F2 = {"rule_id": "R21", "judul": "Memuat pustaka native (.so)", "tingkat": "sedang", "bobot": 30, "bukti": ["lib/x.so"]}


def test_sarif_shape_and_levels():
    s = sarif([("app.apk", F1), ("app.apk", F2)])
    assert s["version"] == "2.1.0" and len(s["runs"][0]["results"]) == 2
    r0 = s["runs"][0]["results"][0]
    assert r0["ruleId"] == "R11" and r0["level"] == "error"
    assert r0["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "app.apk"


def test_exit_code_thresholds():
    assert exit_code([F1, F2], None) == 0          # tanpa --fail-on
    assert exit_code([F2], "sedang") == 1          # sedang == ambang, bukan tinggi -> 1
    assert exit_code([F1, F2], "sedang") == 2      # ada tinggi -> 2
    assert exit_code([F2], "tinggi") == 0          # sedang < tinggi -> lolos


def test_baseline_gates_only_new():
    base = {"temuan": [F2]}                         # R21 sudah ada
    assert [f["rule_id"] for f in temuan_baru([F1, F2], base)] == ["R11"]
