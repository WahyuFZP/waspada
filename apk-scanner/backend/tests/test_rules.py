"""Rule diuji dengan data hasil parse buatan (tanpa APK) supaya cepat dan setiap kasus eksplisit."""
from rules import evaluate

P = "android.permission."
NO_PACKER = {"terdeteksi": False, "detail": [], "info_lain": {}}
TOKEN = "123456789:" + "A" * 35


def parsed(permissions=(), components=(), texts=(), urls=(), ips=(), **extra):
    """extra: package, version_name, sertifikat, manifest, nsc, arsip (rule memakai .get, jadi boleh tidak ada)."""
    return {"permissions": [P + x for x in permissions], "components": list(components), "texts": list(texts),
            "urls": list(urls), "ips": list(ips), **extra}


def ids(p, pk=NO_PACKER):
    return [f.rule_id for f in evaluate(p, pk)]


def test_clean_app_triggers_nothing():
    assert ids(parsed(["INTERNET", "READ_CALENDAR"], urls=["https://schemas.android.com/apk/res/android"])) == []


def test_read_sms_triggers_r01_with_receiver_evidence():
    rcv = {"type": "receiver", "name": ".Sms", "permission": None, "actions": ["android.provider.Telephony.SMS_RECEIVED"]}
    [f] = evaluate(parsed(["RECEIVE_SMS"], [rcv]), NO_PACKER)
    assert f.rule_id == "R01" and f.bobot == 30  # +10: receiver adalah bukti lebih kuat daripada izin saja
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
SMS_RCV = {"type": "receiver", "name": "a.Sms", "permission": None, "actions": ["android.provider.Telephony.SMS_RECEIVED"]}
BOOT_RCV = {"type": "receiver", "name": "a.Boot", "permission": None, "actions": ["android.intent.action.BOOT_COMPLETED"]}


def test_sms_backup_without_aggravators_is_r01_only_at_30():
    # cadangan SMS sah: izin SMS + receiver prioritas 0, tanpa SEND_SMS/boot -> Sedang lewat R01 saja, tidak pernah R15
    p = parsed(["READ_SMS", "RECEIVE_SMS", "READ_CONTACTS"], [SMS_RCV], manifest={"prioritas_receiver": {"a.Sms": 0}})
    [f] = evaluate(p, NO_PACKER)
    assert (f.rule_id, f.bobot) == ("R01", 30)


def test_otp_interceptor_shape_needs_two_aggravators_but_not_combo():
    p = parsed(["RECEIVE_SMS", "SEND_SMS"], [SMS_RCV, BOOT_RCV], manifest={"prioritas_receiver": {"a.Sms": 2147483647}})
    # R15 tidak ikut R07: syaratnya sama dengan R01, jadi aplikasi SMS sah akan selalu kena kombinasi (80 = Tinggi)
    assert ids(p) == ["R01", "R15"]
    [r12] = [f for f in evaluate(p, NO_PACKER) if f.rule_id == "R15"]
    assert r12.bobot == 25 and any("2147483647" in b for b in r12.bukti)
    # satu pemberat saja belum cukup: aplikasi cadangan SMS sah juga sering memasang prioritas tinggi
    assert ids(parsed(["RECEIVE_SMS"], [SMS_RCV], manifest={"prioritas_receiver": {"a.Sms": 999}})) == ["R01"]


def test_impersonation_squat_homoglyph_label_version_and_applink():
    p = parsed(package="id.co.bri.brimo.update", version_name="99.9.9",
               manifest={"label": "ВRImo", "applink_host": ["example-bank.test"]})  # huruf pertama В Cyrillic
    [f] = evaluate(p, NO_PACKER)
    assert (f.rule_id, f.tingkat, f.bobot) == ("R16", "tinggi", 60)
    assert len(f.bukti) == 5


def test_genuine_brand_app_and_unrelated_app_do_not_trigger_r13():
    assert ids(parsed(package="id.co.bri.brimo", manifest={"label": "BRImo"}, sertifikat={"skema": ["v2"], "debug": False})) == []
    assert ids(parsed(package="com.contoh.catatan", version_name="99.9.9", manifest={"label": "Catatan"})) == []  # versi saja bukan peniruan
    # repack: package resmi tetapi ditandatangani kunci debug (kasus "DANA palsu" PRD v1.2)
    assert ids(parsed(package="id.dana", manifest={"label": "DANA"}, sertifikat={"skema": ["v1"], "debug": True})) == ["R16"]


def test_payload_eicar_and_apktool_from_archive():
    ar = {"payload_tersamar": ["assets/config.png: berkas gambar berisi zip"], "payload_eksekusi": ["assets/update.dex: dex"],
          "eicar": ["res/raw/eicar.txt"], "apktool": ["apktool.yml"], "native": []}
    found = {f.rule_id: f.bobot for f in evaluate(parsed(["REQUEST_INSTALL_PACKAGES"], arsip=ar), NO_PACKER)}
    assert found == {"R06": 10, "R17": 40, "R18": 30, "R19": 10}


def test_webview_phishing_combo_vs_lone_bridge():
    phish = ["addJavascriptInterface", "setJavaScriptEnabled", "onReceivedSslError", "proceed", "setAllowFileAccess"]
    [f] = evaluate(parsed(texts=phish), NO_PACKER)
    # di bawah ambang Sedang (30): SDK iklan + OkHttp sah punya string yang sama, jadi R20 tidak memvonis sendirian
    assert (f.rule_id, f.tingkat, f.bobot) == ("R20", "sedang", 25)
    [g] = evaluate(parsed(texts=["addJavascriptInterface"]), NO_PACKER)  # aplikasi hybrid biasa
    assert (g.tingkat, g.bobot) == ("rendah", 10)


def test_network_config_and_manifest_hygiene_are_capped_at_sedang():
    p = parsed(manifest={"cleartext": True, "debuggable": True, "provider_terbuka": ["a.P"], "hijack_task": ["a.Main"]},
               nsc={"cleartext": True, "user_ca": True})
    found = {f.rule_id: f.bobot for f in evaluate(p, NO_PACKER)}
    assert found == {"R21": 30, "R22": 30}  # 45 dan 35 dibatasi 30
    assert ids(parsed(nsc={"cleartext": False, "user_ca": False})) == []  # config pengetat tidak tertandai


def test_anti_analysis_needs_instrumentation_traces():
    rasp = ["/system/bin/su", "isDebuggerConnected", "generic", "google_sdk"]  # juga ada di Firebase Crashlytics
    assert ids(parsed(texts=rasp)) == []
    [g] = evaluate(parsed(texts=rasp + ["frida-server"]), NO_PACKER)
    assert (g.rule_id, g.bobot) == ("R23", 15)


def test_brand_siblings_and_common_words_are_not_impersonation():
    for pkg, label in (("com.whatsapp.w4b", "WhatsApp Business"), ("com.bca.mybca.omni", "myBCA"),
                       ("com.pinjol.cepat", "Dana Cepat"), ("com.resep.app", "Jago Masak")):
        assert "R16" not in ids(parsed(package=pkg, manifest={"label": label})), pkg
    assert "R16" in ids(parsed(package="id.co.bri.brimo.update", manifest={"label": "BRImo"}))


def test_common_capabilities_are_flagged_capability():
    # .so, FCM, identitas: bobot mentah 30 masing-masing, TAPI ditandai kapabilitas=True agar scoring (#4)
    # membatasinya -> sendirian tetap "Rendah", bukan "Tinggi" (lihat tests/test_scoring.py).
    fcm = {"type": "service", "name": "a.Fcm", "permission": None, "actions": ["com.google.firebase.MESSAGING_EVENT"]}
    found = evaluate(parsed(components=[fcm], texts=["android_id"], arsip={"native": ["lib/arm64-v8a/libx.so"]}), NO_PACKER)
    assert [(f.rule_id, f.tingkat, f.bobot) for f in found] == [("R24", "sedang", 30), ("R25", "sedang", 30), ("R26", "sedang", 30)]
    assert all(f.kapabilitas for f in found)


def test_r25_signer_mismatch_on_official_package(monkeypatch):
    import rules
    monkeypatch.setattr(rules, "SIGNER_PINS", {"id.dana": ["aa" * 32]})
    # package resmi + label normal + release-signed ULANG dgn kunci lain -> MISS R16, ditangkap R28
    p = parsed(package="id.dana", manifest={"label": "DANA"},
               sertifikat={"skema": ["v2"], "debug": False, "sha256": "BB" * 32})
    assert {f.rule_id for f in evaluate(p, NO_PACKER)} == {"R28"}  # R16 tak fire (identitas cocok, bukan debug)


def test_r25_official_signer_cancels_impersonation(monkeypatch):
    import rules
    monkeypatch.setattr(rules, "SIGNER_PINS", {"id.dana": ["aa" * 32]})
    # label homoglyph biasanya memicu R16; sidik jari = penerbit resmi -> peniruan dibatalkan, tak ada R28
    p = parsed(package="id.dana", manifest={"label": "ДANA"},
               sertifikat={"skema": ["v2"], "debug": False, "sha256": "AA" * 32})
    assert "R16" not in ids(p) and "R28" not in ids(p)


def test_r25_dormant_without_curated_pin(monkeypatch):
    import rules
    monkeypatch.setattr(rules, "SIGNER_PINS", {})  # belum ada kurasi -> R28 tak pernah menilai
    p = parsed(package="id.dana", manifest={"label": "DANA"},
               sertifikat={"skema": ["v2"], "debug": False, "sha256": "cc" * 32})
    assert "R28" not in ids(p)


def test_edukasi_card_attached_by_rule_id():
    rcv = {"type": "receiver", "name": ".Sms", "permission": None, "actions": ["android.provider.Telephony.SMS_RECEIVED"]}
    [f] = [x for x in evaluate(parsed(["RECEIVE_SMS"], [rcv]), NO_PACKER) if x.rule_id == "R01"]
    assert set(f.edukasi) == {"apa", "kenapa", "dampak"} and "SMS" in f.edukasi["apa"]


def test_corrupt_manifest_flag_triggers_r24():
    [f] = evaluate(parsed(manifest_rusak=True), NO_PACKER)
    assert (f.rule_id, f.tingkat, f.bobot) == ("R27", "sedang", 20)
    assert "R27" not in ids(parsed())  # manifest normal: tidak terpicu
