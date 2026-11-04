"""Adapter CISA KEV: cocokkan katalog kerentanan yang sedang dieksploitasi dengan assets.yaml, kirim ke POST /ingest.

Pakai:  python kev.py                  (unduh katalog terbaru dari CISA)
        python kev.py --file kev.json  (pakai salinan lokal, mis. saat demo tanpa internet)
Polling ulang aman: event per (CVE, host) punya url unik sehingga /ingest membuang duplikat.
"""
import argparse
import json
import logging
import os
from datetime import datetime, timezone

import httpx

from parsers import load_assets

KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


def match_kev(vulns, hosts, now):
    """Record kind=kev untuk setiap pasangan (CVE KEV, host) yang produknya cocok."""
    out = []
    for v in vulns:
        for h in hosts:
            for p in h.get("products", []):
                if v["vendorProject"].lower() == p["vendor"].lower() and p["product"].lower() in v["product"].lower():
                    out.append({
                        "kind": "kev", "timestamp": now, "host": h["host"], "cve": v["cveID"],
                        "vendor": v["vendorProject"], "product": v["product"], "name": v.get("vulnerabilityName"),
                        "date_added": v.get("dateAdded"), "ransomware": v.get("knownRansomwareCampaignUse"),
                    })
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--file", help="file KEV JSON lokal; tanpa ini diunduh dari CISA")
    args = parser.parse_args()

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            catalog = json.load(f)
    else:
        r = httpx.get(KEV_URL, headers={"User-Agent": "Mozilla/5.0 (compatible; WASPADA/1.0)"}, timeout=60)
        r.raise_for_status()
        catalog = r.json()

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    assets = load_assets()
    records = [{**r, "demo": assets["demo"]} for r in match_kev(catalog["vulnerabilities"], assets["hosts"], now)]
    logging.info("KEV %s: %d CVE, %d cocok dengan aset", catalog.get("dateReleased"), len(catalog["vulnerabilities"]), len(records))
    r = httpx.post(f"{args.api}/ingest", json=records, timeout=60, headers={"X-Ingest-Token": os.environ.get("INGEST_TOKEN", "")})
    r.raise_for_status()
    logging.info("ingest -> %s", r.json())


if __name__ == "__main__":
    main()
