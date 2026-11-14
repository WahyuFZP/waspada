from models import Finding
from scoring import score


def f(bobot):
    return Finding("R", "x", "tinggi", bobot)


def test_levels_follow_thresholds():
    assert score([]) == (0, "Rendah")
    assert score([f(20)]) == (20, "Rendah")
    assert score([f(20), f(10)]) == (30, "Sedang")
    assert score([f(20), f(20), f(25)]) == (65, "Tinggi")  # SMS + Aksesibilitas + kombinasi


def test_score_is_capped_at_100():
    assert score([f(30)] * 5) == (100, "Tinggi")


def cap(bobot):
    return Finding("R24", "x", "sedang", bobot, kapabilitas=True)


def test_common_capabilities_alone_stay_rendah():
    # app sah Flutter+Firebase+analitik: 3 kapabilitas (90 bobot mentah) tak boleh jadi "Tinggi"/Berbahaya (#4)
    assert score([cap(30), cap(30), cap(30)]) == (29, "Rendah")


def test_real_findings_still_score_full_despite_capabilities():
    # indikator berisiko nyata tetap dihitung penuh -> deteksi malware tak melemah
    assert score([f(20), f(20), f(25)] + [cap(30), cap(30)]) == (94, "Tinggi")
