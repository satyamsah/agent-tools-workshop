"""
check_setup.py — verify your environment before the workshop.
Run:  python check_setup.py
"""

import sys
import os

errors = []

major, minor = sys.version_info[:2]
if major < 3 or (major == 3 and minor < 10):
    errors.append(f"Python 3.10–3.12 required (you have {major}.{minor})")
elif major == 3 and minor > 12:
    errors.append(f"Python {major}.{minor} not supported — install Python 3.12 via pyenv")
else:
    print(f"✓ Python {major}.{minor}")

from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    errors.append("ANTHROPIC_API_KEY not set — copy .env.example to .env and add your key")
elif not api_key.startswith("sk-ant-"):
    errors.append("ANTHROPIC_API_KEY looks wrong — double-check it")
else:
    print("✓ ANTHROPIC_API_KEY found")

packages = [
    ("anthropic", "anthropic"),
    ("rich", "rich"),
    ("dotenv", "python-dotenv"),
    ("numpy", "numpy"),
    ("faiss", "faiss-cpu"),
    ("sentence_transformers", "sentence-transformers"),
]

for module, pkg in packages:
    try:
        __import__(module)
        print(f"✓ {pkg}")
    except ImportError:
        errors.append(f"{pkg} not installed — run: pip install {pkg}")

db_path = os.path.join(os.path.dirname(__file__), "data", "erp.db")
if not os.path.exists(db_path):
    errors.append("Database not found — run: python data/seed.py")
else:
    print("✓ ERP database found")

if api_key and api_key.startswith("sk-ant-"):
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{"role": "user", "content": "hi"}],
        )
        print("✓ Anthropic API reachable")
    except Exception as e:
        errors.append(f"Anthropic API error: {e}")

print()
if errors:
    print("Setup incomplete — fix these before the workshop:")
    for e in errors:
        print(f"  ✗ {e}")
    sys.exit(1)
else:
    print("All checks passed — you are ready.")
