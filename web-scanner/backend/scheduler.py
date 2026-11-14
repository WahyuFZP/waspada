"""Pemicu penjadwal re-scan (#19). Hanya MEMICU endpoint; semua kerja (scan pasif, diff, regresi,
otorisasi yang sudah direkam) ada di server.

  python scheduler.py --once                 # satu lintasan — cocok untuk cron/launchd
  python scheduler.py --loop 3600            # ulangi tiap 3600 detik (min 60)

Penjadwalan sebenarnya sebaiknya diserahkan ke OS. Contoh crontab (tiap jam):
  0 * * * * /path/.venv/bin/python /path/scheduler.py --once >> /path/jadwal.log 2>&1
"""
import argparse
import sys
import time

import httpx


def jalankan(base):
    r = httpx.post(f"{base}/jadwal/jalankan", timeout=600)
    r.raise_for_status()
    h = r.json()
    print(f"{h['dijalankan']} jadwal dijalankan.")
    for row in h.get("hasil", []):
        tanda = "⚠ REGRESI" if row["status"] == "regresi" else row["status"]
        print(f"  [{tanda}] {row['target']} — {row.get('detail', '')}")
    return h


def main(argv=None):
    ap = argparse.ArgumentParser(description="Pemicu penjadwal re-scan web (#19).")
    ap.add_argument("--base", default="http://localhost:8002", help="alamat web-scanner (default :8002)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--once", action="store_true", help="satu lintasan lalu keluar (untuk cron)")
    g.add_argument("--loop", type=float, metavar="DETIK", help="ulangi tiap DETIK (min 60)")
    a = ap.parse_args(argv)

    if a.once:
        jalankan(a.base)
        return 0
    while True:
        try:
            jalankan(a.base)
        except httpx.HTTPError as e:  # server mati/lambat: catat, lanjut lintasan berikutnya
            print(f"gagal memicu: {type(e).__name__}", file=sys.stderr)
        time.sleep(max(a.loop, 60))


if __name__ == "__main__":
    sys.exit(main())
