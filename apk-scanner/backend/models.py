from dataclasses import dataclass, field


@dataclass
class Finding:
    rule_id: str
    judul: str
    tingkat: str  # rendah | sedang | tinggi
    bobot: int
    bukti: list[str] = field(default_factory=list)
    penjelasan: str = ""
