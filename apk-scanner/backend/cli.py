"""Jalankan pipeline analisis dari terminal, tanpa API/Docker: python cli.py app.apk [app2.apk ...].

Mencetak satu baris per APK dengan token VERDICT= (clean|suspicious|malicious <- Rendah|Sedang|Tinggi) sehingga
bisa dinilai langsung oleh run_scan.py milik korpus fixture. APKiD yang tidak terpasang dicatat, tidak menggagalkan.
"""
import sys

import packer
import parser as apk_parser
import rules
import scoring

VERDICT = {"Rendah": "clean", "Sedang": "suspicious", "Tinggi": "malicious"}

for path in sys.argv[1:]:
    parsed = apk_parser.parse(path)
    findings = rules.evaluate(parsed, packer.scan(path))
    skor, level = scoring.score(findings)
    temuan = ", ".join(f"{f.rule_id}({f.bobot})" for f in findings) or "-"
    print(f"VERDICT={VERDICT[level]} skor={skor} level={level}  {path.rsplit('/', 1)[-1]}  [{temuan}]")
