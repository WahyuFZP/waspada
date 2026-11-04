"""Replay skenario sintetis (JSONL, satu record per baris: artikel, log auth, Suricata, KEV) ke POST /ingest.

Demo deterministik: natuna.jsonl (OSINT berita), intrusi.jsonl (log internal + CISA KEV).
"""
import argparse
import json
import os
import time

import httpx

parser = argparse.ArgumentParser()
parser.add_argument("scenario")
parser.add_argument("--api", default="http://localhost:8000")
parser.add_argument("--delay", type=float, default=1.5, help="jeda antar artikel (detik) supaya terlihat satu per satu")
args = parser.parse_args()

with open(args.scenario, encoding="utf-8") as f:
    articles = [json.loads(line) for line in f if line.strip()]

for article in articles:
    r = httpx.post(f"{args.api}/ingest", json=article, timeout=15, headers={"X-Ingest-Token": os.environ.get("INGEST_TOKEN", "")})
    r.raise_for_status()
    result = r.json()
    # artikel punya title; log auth punya line; Suricata punya alert.signature; KEV punya cve
    label = article.get("title") or article.get("line") or (article.get("alert") or {}).get("signature") or article.get("cve")
    print(f"{article['timestamp']} {article.get('source') or article.get('kind', ''):<8} {label}")
    print(f"    -> {result['events']} event, {len(result['alerts'])} alert"
          + (" (duplikat, dilewati)" if result["skipped_duplicates"] else ""))
    time.sleep(args.delay)
