"""Parser log keamanan -> event ternormalisasi. Satu fungsi per sumber; sumber baru cukup menambah fungsi di sini.

Semua input datang dari luar (agen, skrip, feed), jadi divalidasi di sini sebelum masuk engine.
"""
import ipaddress
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

CVE_RE = re.compile(r"CVE-\d{4}-\d{4,7}", re.I)
# Format syslog sshd standar (OpenSSH): "Oct 21 09:15:03 srv-web-01 sshd[812]: Failed password for root from 203.0.113.50 port 51122 ssh2"
SSHD_RE = re.compile(
    r"^(?P<stamp>\w{3}\s+\d{1,2} \d{2}:\d{2}:\d{2}) (?P<host>\S+) sshd\[\d+\]: "
    r"(?P<result>Failed|Accepted) (?P<method>\S+) for (?:invalid user )?(?P<user>\S+) from (?P<ip>\S+) port \d+"
)


def load_assets(path=Path(__file__).with_name("assets.yaml")):
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    hosts = data["hosts"]
    return {"hosts": hosts, "by_ip": {h["ip"]: h["host"] for h in hosts}, "demo": bool(data.get("demo"))}


def _ip(value, field):
    try:
        return str(ipaddress.ip_address(str(value)))
    except ValueError:
        raise ValueError(f"{field} bukan alamat IP yang valid: {value!r}")


def _iso(ts):
    return ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_auth(record, parse_ts):
    """Baris auth.log sshd. Baris lain (session opened, dll.) bukan kejadian login, jadi diabaikan."""
    line = record.get("line")
    if not isinstance(line, str):
        raise ValueError("record auth butuh field 'line' berupa teks log")
    m = SSHD_RE.match(line.strip())
    if not m:
        return []
    if record.get("timestamp"):
        ts = parse_ts(record["timestamp"])
    else:
        # syslog tidak menyimpan tahun; shortcut: anggap tahun berjalan (UTC), keliru untuk log lintas tahun baru
        ts = datetime.strptime(f"{datetime.now(timezone.utc).year} {m['stamp']}", "%Y %b %d %H:%M:%S").replace(tzinfo=timezone.utc)
    ok = m["result"] == "Accepted"
    src_ip = _ip(m["ip"], "src_ip")
    return [{
        "timestamp": _iso(ts),
        "source": "auth",
        "event_type": "auth.success" if ok else "auth.failed",
        "host": m["host"],
        "user": m["user"],
        "src_ip": src_ip,
        "title": f"Login SSH {'berhasil' if ok else 'gagal'}: user {m['user']} dari {src_ip}",
        "raw": record,
    }]


def parse_suricata(record, parse_ts, assets):
    """Satu baris eve.json Suricata. Hanya event_type 'alert' yang menjadi event."""
    if record.get("event_type") != "alert":
        return []
    alert = record.get("alert")
    if not isinstance(alert, dict) or not isinstance(alert.get("signature"), str):
        raise ValueError("alert Suricata butuh alert.signature")
    signature = alert["signature"]
    category = str(alert.get("category", ""))
    src_ip, dest_ip = _ip(record.get("src_ip"), "src_ip"), _ip(record.get("dest_ip"), "dest_ip")
    meta = alert.get("metadata") if isinstance(alert.get("metadata"), dict) else {}
    meta_cves = [c for c in meta.get("cve", []) if isinstance(c, str)] if isinstance(meta.get("cve"), list) else []
    port = record.get("dest_port")
    if port is not None and not (isinstance(port, int) and 0 <= port <= 65535):
        raise ValueError(f"dest_port tidak valid: {port!r}")
    cves = sorted({c.upper() for c in CVE_RE.findall(signature) + meta_cves})

    text = f"{signature} {category}".upper()
    if "SCAN" in text:
        event_type = "ids.scan"
    elif cves or "EXPLOIT" in text or "ATTACK" in text:
        event_type = "ids.exploit_attempt"
    else:
        event_type = "ids.alert"
    return [{
        "timestamp": _iso(parse_ts(record["timestamp"])),
        "source": "suricata",
        "event_type": event_type,
        "host": assets["by_ip"].get(dest_ip, dest_ip),  # IP di luar inventaris tetap terlihat apa adanya
        "src_ip": src_ip,
        "dest_port": port,
        "cve": cves[0] if cves else None,
        "title": signature,
        "raw": record,
    }]


def parse_kev(record, parse_ts):
    """Kecocokan aset x katalog CISA KEV, dibuat oleh kev.py."""
    for field in ("timestamp", "host", "cve", "vendor", "product"):
        if not record.get(field):
            raise ValueError(f"record kev butuh field {field}")
    cve = str(record["cve"]).upper()
    if not CVE_RE.fullmatch(cve):
        raise ValueError(f"cve tidak valid: {cve!r}")
    ransomware = record.get("ransomware") == "Known"
    return [{
        "timestamp": _iso(parse_ts(record["timestamp"])),
        "source": "cisa_kev",
        "event_type": "vuln.kev_match",
        "host": record["host"],
        "cve": cve,
        "title": f"{cve} ({record['vendor']} {record['product']}) dieksploitasi aktif"
                 + (", dipakai kampanye ransomware" if ransomware else "")
                 + f". Aset {record['host']} memakai produk ini, perlu verifikasi versi.",
        # url per host supaya polling ulang kev.py tidak menggandakan event (dedupe by url di /ingest)
        "url": f"https://nvd.nist.gov/vuln/detail/{cve}#{record['host']}",
        "raw": record,
    }]
