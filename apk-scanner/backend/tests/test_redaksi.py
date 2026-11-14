"""Tes redaksi rahasia di bukti (#11): samarkan yang sensitif, jangan over-masking yang bukan rahasia."""
from redaksi import redaksi


def test_cookie_value_masked_flags_kept():
    assert redaksi("SESSIONID=8f3b2a1c9d4e; Path=/; SameSite=None") == "SESSIONID=8f3b…; Path=/; SameSite=None"


def test_query_secret_masked():
    assert redaksi("https://evil/c2?token=abcdef123456") == "https://evil/c2?token=abcd…"


def test_email_and_phone_masked():
    assert redaksi("kontak admin@contoh.co.id 081234567890") == "kontak ad…@contoh.co.id 0812…"


def test_non_secret_not_over_masked():
    assert redaksi("8.8.4.4") == "8.8.4.4"            # IP publik (bukti R09) tidak disamarkan
    assert redaksi("lib/arm64-v8a/libx.so") == "lib/arm64-v8a/libx.so"


def test_already_masked_telegram_untouched():
    assert redaksi("api.telegram.org/bot123456789:AAA…AAA") == "api.telegram.org/bot123456789:AAA…AAA"
