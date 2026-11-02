"""Rule diuji dengan data hasil parse buatan (tanpa APK) supaya cepat dan setiap kasus eksplisit."""
from rules import evaluate

P = "android.permission."
NO_PACKER = {"terdeteksi": False, "detail": [], "info_lain": {}}
TOKEN = "123456789:" + "A" * 35


def parsed(permissions=(), components=(), texts=(), urls=(), ips=()):
    return {"permissions": [P + x for x in permissions], "components": list(components), "texts": list(texts),
            "urls": list(urls), "ips": list(ips)}


def ids(p, pk=NO_PACKER):
    return [f.rule_id for f in evaluate(p, pk)]


def test_clean_app_triggers_nothing():
    assert ids(parsed(["INTERNET", "READ_CALENDAR"], urls=["https://schemas.android.com/apk/res/android"])) == []


def test_read_sms_triggers_r01_with_receiver_evidence():
    rcv = {"type": "receiver", "name": ".Sms", "permission": None, "actions": ["android.provider.Telephony.SMS_RECEIVED"]}
    [f] = evaluate(parsed(["RECEIVE_SMS"], [rcv]), NO_PACKER)
    assert f.rule_id == "R01" and f.bobot == 20
    assert "receiver .Sms: android.provider.Telephony.SMS_RECEIVED" in f.bukti


def test_accessibility_detected_from_service_attribute_without_uses_permission():
    svc = {"type": "service", "name": ".Acc", "permission": P + "BIND_ACCESSIBILITY_SERVICE", "actions": []}
    assert ids(parsed([], [svc])) == ["R02"]
    by_action = {"type": "service", "name": ".Acc", "permission": None,
                 "actions": ["android.accessibilityservice.AccessibilityService"]}
    assert ids(parsed([], [by_action])) == ["R02"]


def test_sms_plus_accessibility_is_banking_trojan_combo():
    svc = {"type": "service", "name": ".Acc", "permission": P + "BIND_ACCESSIBILITY_SERVICE", "actions": []}
    assert ids(parsed(["READ_SMS"], [svc])) == ["R01", "R02", "R07"]


def test_notification_listener_and_device_admin():
    notif = {"type": "service", "name": ".N", "permission": P + "BIND_NOTIFICATION_LISTENER_SERVICE", "actions": []}
    admin = {"type": "receiver", "name": ".A", "permission": None, "actions": ["android.app.action.DEVICE_ADMIN_ENABLED"]}
    assert ids(parsed(["SYSTEM_ALERT_WINDOW", "REQUEST_INSTALL_PACKAGES"], [notif, admin])) == ["R03", "R04", "R05", "R06", "R07"]


def test_packer_only_from_suspicious_categories():
    assert ids(parsed(), {"terdeteksi": False, "detail": [], "info_lain": {"compiler": ["r8 without marker (suspicious)"]}}) == []
    assert ids(parsed(), {"terdeteksi": True, "detail": ["Jiagu"], "info_lain": {}}) == ["R08"]


def test_r09_public_ip_and_shortlink_but_not_common_domains():
    assert ids(parsed(urls=["https://www.google.com/x", "http://schemas.android.com/apk"], ips=["10.0.0.1", "127.0.0.1"])) == []
    assert ids(parsed(urls=["http://203.0.113.10/x"], ips=["203.0.113.10"])) == []  # TEST-NET bukan IP global
    assert ids(parsed(urls=["http://8.8.4.4/up"], ips=["8.8.4.4"])) == ["R09"]
    assert ids(parsed(urls=["https://bit.ly/abc"])) == ["R09"]


def test_send_sms_needs_permission_and_api():
    assert ids(parsed(["SEND_SMS"])) == []  # izin saja tanpa pemanggilan API belum cukup
    assert ids(parsed(["SEND_SMS"], texts=["sendTextMessage"])) == ["R10"]


def test_telegram_bot_detected_and_token_masked():
    [f] = evaluate(parsed(texts=[f"https://api.telegram.org/bot{TOKEN}/sendMessage"]), NO_PACKER)
    assert f.rule_id == "R11" and f.bobot == 30
    assert all(TOKEN not in b for b in f.bukti)  # token asli tidak boleh ikut ke laporan
    assert f.bukti == ["api.telegram.org/bot123456789:AAA…AAA"]
    # token berdiri sendiri (mis. di resources) juga tertangkap dan disamarkan
    [g] = evaluate(parsed(texts=[f"token={TOKEN}"]), NO_PACKER)
    assert g.bukti == ["123456789:AAA…AAA"]


# R12–R14: pola dari analisis APK judi online nyata (pgbet.apk); teks di bawah buatan sendiri, bukan salinan APK itu
GAMBLING_UI = ['{"4d_lottery": "4D Lottery", "casino": "Casino", "deposit": "Deposit", "withdraw": "Tarik Dana"}']


def test_gambling_app_triggers_r12():
    [f] = evaluate(parsed(texts=GAMBLING_UI), NO_PACKER)
    assert f.rule_id == "R12" and f.tingkat == "tinggi"
    # kunci dan nilai JSON sama-sama dihitung; "4d_lottery" tidak, karena "_" bukan batas kata
    assert f.bukti == ["casino ×2", "lottery ×1", "deposit ×2", "withdraw ×1", "tarik dana ×1"]


def test_bank_app_vocabulary_is_not_gambling():
    # aplikasi bank sah: setor/tarik dan bonus, tetapi tanpa istilah taruhan
    texts = ["Deposit ke rekening", "Withdraw ke bank", "Bonus poin", "Jadwal slot waktu"]
    assert ids(parsed(texts=texts)) == []


def test_single_gambling_word_is_not_enough():
    assert ids(parsed(texts=["Jackpot!", "Deposit"])) == []


def test_bundled_secrets_report_key_names_only():
    env = "API_URL='https://api.example.org'\nBITLY_TOKEN='abcdef0123456789'\nSECRET_KEY='Zz9Yy8Xx7Ww6'\n" \
          "SMARTICO_SALT_KEY='null'\nFB_CLIENT_TOKEN=''\nOPEN_TELEMETRY_AUTHORIZATION_HEADER='Basic Y2xpZW50OnNlY3JldA=='\n"
    [f] = evaluate(parsed(texts=[env]), NO_PACKER)
    assert f.rule_id == "R13"
    assert f.bukti == ["BITLY_TOKEN", "OPEN_TELEMETRY_AUTHORIZATION_HEADER", "SECRET_KEY"]  # null/kosong diabaikan
    assert not any("abcdef" in b or "Basic" in b for b in f.bukti)  # nilai rahasia tidak pernah bocor ke laporan


def test_anti_emulator_checks_trigger_r14_but_compiler_marker_does_not():
    pk = {"terdeteksi": False, "detail": [], "info_lain": {"compiler": ["r8"], "anti_vm": ["Build.FINGERPRINT check"]}}
    [f] = evaluate(parsed(), pk)
    assert f.rule_id == "R14" and f.bukti == ["anti_vm: Build.FINGERPRINT check"]


def test_short_gy_subdomain_counts_as_shortener():
    assert ids(parsed(urls=["https://4cqx.short.gy/85d30e"])) == ["R09"]
