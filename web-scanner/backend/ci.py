"""Transformasi output untuk gerbang CI/CD (#9): SARIF 2.1.0, diff baseline, exit-code.
Tidak mengubah deteksi — hanya menyajikan ulang temuan dari laporan yang sudah ada."""
RANK = {"info": 0, "rendah": 1, "sedang": 2, "tinggi": 3, "kritis": 4}
_LEVEL = {"kritis": "error", "tinggi": "error", "sedang": "warning", "rendah": "note", "info": "note"}


def sarif(rep):
    """Laporan web -> SARIF 2.1.0 (format standar code-scanning, mis. GitHub Actions)."""
    temuan = rep.get("temuan", [])
    results = [{
        "ruleId": f["id"],
        "level": _LEVEL.get(f["tingkat"], "warning"),
        "message": {"text": f"{f['judul']} — {f['perbaikan']}"},
        "locations": [{"physicalLocation": {"artifactLocation": {"uri": f.get("lokasi") or rep.get("target", "")}}}],
        "properties": {"cwe": f.get("cwe", ""), "tingkat": f["tingkat"]},
    } for f in temuan]
    rules_meta = [{"id": i} for i in dict.fromkeys(f["id"] for f in temuan)]
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "WASPADA Web Scanner", "version": rep.get("schema_version", ""),
                                      "rules": rules_meta}}, "results": results}],
    }


def temuan_baru(rep, baseline):
    """Temuan yang ada sekarang tapi TIDAK di baseline (gerbang regresi, bukan utang lama)."""
    lama = {(f["id"], f["judul"]) for f in baseline.get("temuan", [])}
    return [f for f in rep.get("temuan", []) if (f["id"], f["judul"]) not in lama]


def exit_code(temuan, fail_on):
    """0 bila tak ada yang mencapai ambang fail_on; 2 bila ada tinggi/kritis, 1 bila sedang."""
    if not fail_on or not temuan:
        return 0
    worst = max(RANK[f["tingkat"]] for f in temuan)
    if worst < RANK[fail_on]:
        return 0
    return 2 if worst >= RANK["tinggi"] else 1
