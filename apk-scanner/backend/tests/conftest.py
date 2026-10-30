import hashlib
import os
import sys
import urllib.request
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# APK uji resmi dari repo Androguard (Apache-2.0), aplikasi sah dari F-Droid. Diunduh ke /tmp saat test,
# tidak disimpan di repo. Checksum dipin agar file yang berubah atau tertukar langsung ketahuan.
BASE = "https://raw.githubusercontent.com/androguard/androguard/v4.1.4/tests/data/APK/"
FIXTURES = {
    "com.politedroid_4.apk": "c809bdff83715fbf919f3840ee09869b038e209378b906e135ee40d3f0e1f075",
    "com.teleca.jamendo_35.apk": "44e880a1e6c64a5a273fcdb568054bc298669377e60302f0b97ccd13ffb33b6d",
}
CACHE = Path(os.environ.get("APK_FIXTURE_DIR", "/tmp/apk-fixtures"))


@pytest.fixture(scope="session")
def benign_apk():
    def get(name):
        CACHE.mkdir(parents=True, exist_ok=True)
        path = CACHE / name
        if not path.exists():
            try:
                urllib.request.urlretrieve(BASE + name, path)
            except OSError as exc:
                pytest.skip(f"fixture {name} tidak bisa diunduh: {exc}")
        expected = FIXTURES[name]
        if expected:
            assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, f"checksum {name} berubah"
        return str(path)
    return get
