"""Tes transformasi gerbang CI (#9) web: SARIF, baseline, exit-code. Tanpa jaringan."""
from ci import exit_code, sarif, temuan_baru

REP = {"target": "https://x.example", "schema_version": "web-0.1", "temuan": [
    {"id": "W-H03", "judul": "Berkas sensitif terekspos: /.env", "tingkat": "kritis", "perbaikan": "hapus", "lokasi": "https://x.example/.env", "cwe": "CWE-538"},
    {"id": "W-H05", "judul": "X-Content-Type-Options tidak ada", "tingkat": "rendah", "perbaikan": "set nosniff", "lokasi": "https://x.example", "cwe": "CWE-16"},
]}


def test_sarif_shape_and_levels():
    s = sarif(REP)
    assert s["version"] == "2.1.0" and len(s["runs"][0]["results"]) == 2
    lvl = {r["ruleId"]: r["level"] for r in s["runs"][0]["results"]}
    assert lvl == {"W-H03": "error", "W-H05": "note"}  # kritis->error, rendah->note


def test_exit_code_thresholds():
    assert exit_code(REP["temuan"], None) == 0           # tanpa --fail-on: tak pernah menggagalkan
    assert exit_code(REP["temuan"], "rendah") == 2       # ada kritis -> 2
    assert exit_code(REP["temuan"], "kritis") == 2       # kritis == ambang
    assert exit_code([REP["temuan"][1]], "sedang") == 0  # rendah < sedang -> lolos
    assert exit_code([REP["temuan"][1]], "rendah") == 1  # rendah == ambang, bukan tinggi -> 1


def test_baseline_gates_only_new():
    base = {"temuan": [REP["temuan"][1]]}                # hanya W-H05 yang sudah ada
    assert [f["id"] for f in temuan_baru(REP, base)] == ["W-H03"]  # W-H03 baru -> digerbang
