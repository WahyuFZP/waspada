"""Correlation engine: sliding window per (rule, group), rule = urutan langkah dari rules.yaml."""
import uuid
from datetime import timedelta
from pathlib import Path

import yaml

from normalize import parse_ts

UNITS = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}


def parse_window(text):
    return timedelta(**{UNITS[text[-1]]: int(text[:-1])})


def load_rules(path=Path(__file__).with_name("rules.yaml")):
    rules = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    for r in rules:
        r["window"] = parse_window(r["window"])
        if not r.get("steps"):
            raise ValueError(f"rule tanpa steps: {r['name']}")
    return rules


def matches(event, match):
    return all(event.get(k) in (v if isinstance(v, list) else [v]) for k, v in match.items())


def satisfied(events, steps):
    """Kembalikan event pendukung jika semua langkah terpenuhi berurutan, else None."""
    support, i = [], 0
    for step in steps:
        hits = []
        while i < len(events):
            e = events[i]
            i += 1
            if not matches(e, step["match"]):
                continue
            hits.append(e)
            enough = len(hits) >= step.get("count", 1)
            if step.get("distinct"):
                enough = enough and len({h[step["distinct"]] for h in hits}) >= step.get("min_distinct", 1)
            if enough:
                break
        else:
            return None
        support += hits
    return support


class Engine:
    def __init__(self, rules):
        self.rules = rules
        self.buffers = {}  # (rule name, group key) -> events dalam window, urut timestamp

    def process(self, event):
        """Masukkan satu event, kembalikan list alert baru."""
        alerts = []
        for rule in self.rules:
            if not any(matches(event, s["match"]) for s in rule["steps"]):
                continue
            group = {g: event.get(g) for g in rule["group_by"]}
            key = (rule["name"], tuple(group.values()))
            buf = self.buffers.setdefault(key, [])
            buf.append(event)
            buf.sort(key=lambda e: e["timestamp"])  # format timestamp seragam -> urut leksikal = urut waktu
            newest = parse_ts(buf[-1]["timestamp"])
            buf[:] = [e for e in buf if parse_ts(e["timestamp"]) >= newest - rule["window"]]

            support = satisfied(buf, rule["steps"])
            if support:
                buf.clear()  # satu rangkaian = satu alert; rangkaian berikutnya mulai dari nol
                alerts.append({
                    "id": uuid.uuid4().hex,
                    "rule": rule["name"],
                    "severity": rule["severity"],
                    "mitre": rule.get("mitre", []),  # [{id, name}] teknik MITRE ATT&CK, dari rules.yaml
                    "group": group,
                    "timestamp": support[-1]["timestamp"],
                    "events": support,
                })
        return alerts
