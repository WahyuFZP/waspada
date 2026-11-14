"""Tes redaksi rahasia di bukti (#11): samarkan yang sensitif, jangan over-masking yang bukan rahasia."""
from redaksi import redaksi


def test_cookie_value_masked_flags_kept():
    assert redaksi("SESSIONID=8f3b2a1c9d4e; Path=/; SameSite=None") == "SESSIONID=8f3b…; Path=/; SameSite=None"


def test_query_secret_masked():
    assert redaksi("https://x/c2?api_key=SECRET123&id=5") == "https://x/c2?api_key=SECR…&id=5"


def test_email_and_phone_masked():
    assert redaksi("kontak user@example.com 081234567890") == "kontak us…@example.com 0812…"


def test_non_secret_not_over_masked():
    assert redaksi("Strict-Transport-Security: max-age=31536000") == "Strict-Transport-Security: max-age=31536000"
    assert redaksi("Server: nginx/1.18.0") == "Server: nginx/1.18.0"
    assert redaksi("GET /.env -> 200 dengan isi cocok") == "GET /.env -> 200 dengan isi cocok"


def test_already_masked_telegram_untouched():
    assert redaksi("api.telegram.org/bot123456789:AAA…AAA") == "api.telegram.org/bot123456789:AAA…AAA"
