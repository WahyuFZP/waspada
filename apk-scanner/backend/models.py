from dataclasses import dataclass, field


@dataclass
class Finding:
    rule_id: str
    judul: str
    tingkat: str  # rendah | sedang | tinggi
    bobot: int
    bukti: list[str] = field(default_factory=list)
    penjelasan: str = ""
    kapabilitas: bool = False  # R21-R23: kapabilitas umum (native/FCM/identitas); dibatasi di scoring (#4)
    edukasi: dict = field(default_factory=dict)  # kartu "Pelajari dulu" {apa, kenapa, dampak} (opsional, #8)
