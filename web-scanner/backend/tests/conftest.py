import sys
from pathlib import Path

# agar test bisa `import rules`/`main` dari backend/ (pola sama dengan apk-scanner/backend/tests/conftest.py)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
