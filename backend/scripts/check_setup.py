"""Dependency/download diagnostics only; prints no configuration secrets."""
import importlib.util
import os
import sys
import urllib.request

print("Python:", sys.version.split()[0])
print("Virtual environment:", sys.prefix != sys.base_prefix)
for module in ("fastapi", "uvicorn", "sqlmodel", "sqlalchemy", "pydantic", "anthropic",
               "httpx", "dotenv", "psycopg", "alembic", "tzdata", "pytest"):
    print(module + ":", "installed" if importlib.util.find_spec(module) else "missing")
for option in ("PIP_NO_INDEX", "PIP_INDEX_URL", "PIP_EXTRA_INDEX_URL", "PIP_CONFIG_FILE"):
    print(option + ":", "set (value withheld)" if option in os.environ else "not set")
try:
    with urllib.request.urlopen("https://pypi.org/simple/fastapi/", timeout=8) as response:
        content = response.read()
        print("Public PyPI status:", response.status)
        print("fastapi 0.128.0 listed:", b"0.128.0" in content)
except Exception as exc:
    reason = getattr(exc, "reason", exc)
    # Class and errno identify network/TLS errors without URLs/proxy credentials.
    print("Public PyPI check failed:", type(reason).__name__)
    print("Error number:", getattr(reason, "errno", None))
    print("Windows error number:", getattr(reason, "winerror", None))
    raise SystemExit(1)
