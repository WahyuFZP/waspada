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
