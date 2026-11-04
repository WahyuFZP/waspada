"""Transformasi output untuk gerbang CI/CD (#9): SARIF 2.1.0, diff baseline, exit-code.
Tidak mengubah deteksi — hanya menyajikan ulang temuan yang sudah dihasilkan."""
RANK = {"rendah": 0, "sedang": 1, "tinggi": 2}
_LEVEL = {"tinggi": "error", "sedang": "warning", "rendah": "note"}


def sarif(pasangan):
    """pasangan: list[(uri_apk, temuan_dict)] -> SARIF 2.1.0 (format standar code-scanning)."""
    results = [{
        "ruleId": f["rule_id"],
        "level": _LEVEL.get(f["tingkat"], "warning"),
        "message": {"text": f"{f['judul']}: {'; '.join(f['bukti'])}" if f.get("bukti") else f["judul"]},
        "locations": [{"physicalLocation": {"artifactLocation": {"uri": uri}}}],
        "properties": {"bobot": f.get("bobot", 0), "tingkat": f["tingkat"]},
    } for uri, f in pasangan]
    rules_meta = [{"id": i} for i in dict.fromkeys(f["rule_id"] for _, f in pasangan)]
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "WASPADA APK Scanner", "rules": rules_meta}}, "results": results}],
    }


def temuan_baru(temuan, baseline):
    """temuan: list[dict] -> yang TIDAK ada di baseline (gerbang regresi, bukan utang lama)."""
    lama = {(f["rule_id"], f["judul"]) for f in baseline.get("temuan", [])}
    return [f for f in temuan if (f["rule_id"], f["judul"]) not in lama]


def exit_code(temuan, fail_on):
    """0 bila tak ada yang mencapai ambang fail_on; 2 bila ada tinggi, 1 bila sedang."""
    if not fail_on or not temuan:
        return 0
    worst = max(RANK[f["tingkat"]] for f in temuan)
    if worst < RANK[fail_on]:
        return 0
    return 2 if worst >= RANK["tinggi"] else 1
