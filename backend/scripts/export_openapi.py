"""Print the actual FastAPI OpenAPI export; does not connect to providers or DB."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import app
print(json.dumps(app.openapi(), indent=2, sort_keys=True))
