"""Useful dependency-free checks, separate from the full FastAPI/SQLModel pytest suite."""
import ast
import asyncio
import json
import math
import runpy
import unittest
from datetime import datetime, date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BMI = runpy.run_path(str(ROOT/"app/bmi.py"))
OPENAPI = json.loads((ROOT/"openapi.json").read_text(encoding="utf-8"))

def validate(value, schema):
    if "$ref" in schema:
        return validate(value, OPENAPI["components"]["schemas"][schema["$ref"].split("/")[-1]])
    if "anyOf" in schema:
        for option in schema["anyOf"]:
            try:
                validate(value, option)
                return
            except (AssertionError, ValueError, TypeError):
                pass
        raise AssertionError("No matching union type")
    kind = schema.get("type")
    if kind == "null":
        assert value is None
    elif kind == "object":
        assert isinstance(value, dict)
        assert set(schema.get("required", [])) <= value.keys()
        for key, item in value.items():
            if key in schema.get("properties", {}):
                validate(item, schema["properties"][key])
            elif isinstance(schema.get("additionalProperties"), dict):
                validate(item, schema["additionalProperties"])
            elif schema.get("additionalProperties") is False:
                raise AssertionError("Unexpected field")
    elif kind == "array":
        assert isinstance(value, list)
        for item in value:
            validate(item, schema.get("items", {}))
        assert len(value) >= schema.get("minItems", 0)
        assert len(value) <= schema.get("maxItems", math.inf)
    elif kind == "integer":
        assert type(value) is int
    elif kind == "number":
        assert type(value) in (int, float) and math.isfinite(value)
    elif kind == "boolean":
        assert type(value) is bool
    elif kind == "string":
        assert isinstance(value, str)
        if schema.get("format") == "date":
            date.fromisoformat(value)
        if schema.get("format") == "date-time":
            assert datetime.fromisoformat(value).tzinfo is not None
    if "enum" in schema:
        assert value in schema["enum"]

class DependencyFreeChecks(unittest.TestCase):
    def test_bmi_existing_rounding_and_categories(self):
        self.assertEqual(BMI["bmi_formula"](180, 74.6), 23.0)
        self.assertEqual([BMI["category"](n) for n in (18.4, 18.5, 25, 30)],
                         ["Underweight", "Normal", "Overweight", "Obese"])

    def test_bmi_rejects_invalid(self):
        for h, w in ((0, 70), (-1, 70), (180, 0), (math.nan, 70), (180, math.inf)):
            with self.subTest(h=h, w=w):
                with self.assertRaises(ValueError):
                    BMI["bmi_formula"](h, w)

    def test_missing_bmi(self):
        self.assertEqual(asyncio.run(BMI["compute_bmi"](None, 70)), (None, None, "formula"))
        self.assertEqual(asyncio.run(BMI["compute_bmi"](180, None)), (None, None, "formula"))

    def test_all_source_compiles(self):
        files = list((ROOT/"app").glob("*.py"))+list((ROOT/"agent").glob("*.py"))+list((ROOT/"tests").glob("*.py"))
        files += list((ROOT/"migrations").rglob("*.py"))+list((ROOT/"scripts").glob("*.py"))
        for path in files:
            with self.subTest(path=path.name):
                compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_all_fixture_json_and_contract_shapes(self):
        shapes = {"profile": "UserOut", "today": "TodayOut", "chat": "ChatOut", "proposal": "ChatOut",
                  "food": "FoodDayOut", "visualize-session": "SessionToken"}
        arrays = {"workouts": "WorkoutOut", "diet-plans": "DietOut", "goals": "GoalOut",
                  "scans": "ScanOut", "chat-history": "ChatMessageOut"}
        for path in (ROOT/"fixtures").glob("*.json"):
            with self.subTest(path=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                if path.stem in shapes:
                    validate(data, {"$ref": "#/components/schemas/"+shapes[path.stem]})
                elif path.stem in arrays:
                    validate(data, {"type": "array", "items": {"$ref": "#/components/schemas/"+arrays[path.stem]}})

    def test_openapi_routes_security_and_optional_keys(self):
        expected = {"/health", "/profile", "/today", "/chat", "/chat/history", "/workouts",
                    "/workouts/{id}", "/workouts/{id}/start", "/workouts/{id}/finish",
                    "/exercises/{id}/sets", "/sets/{id}", "/food", "/food/{id}", "/diet-plans", "/goals", "/goals/{id}",
                    "/visualize/session", "/scans", "/cards", "/cards/{id}/apply", "/sessions", "/sessions/{id}"}
        self.assertEqual(set(OPENAPI["paths"]), expected)
        for path, methods in OPENAPI["paths"].items():
            for method, op in methods.items():
                if path != "/health":
                    self.assertEqual(op["security"], [{"HTTPBearer": []}])
                for param in op.get("parameters", []):
                    if param["name"] == "Idempotency-Key":
                        self.assertFalse(param["required"])

    def test_model_migration_columns_match(self):
        model_ast = ast.parse((ROOT/"app/models.py").read_text(encoding="utf-8"))
        classes = {n.name: n for n in model_ast.body if isinstance(n, ast.ClassDef)}
        def columns(cls):
            result = {n.target.id for n in cls.body if isinstance(n, ast.AnnAssign)}
            if any(isinstance(b, ast.Name) and b.id == "Owned" for b in cls.bases):
                result |= columns(classes["Owned"])
            return result
        expected = {n.lower(): columns(c) for n, c in classes.items() if n != "Owned"}
        migration = ast.parse((ROOT/"migrations/versions/0001_milo.py").read_text(encoding="utf-8"))
        upgrade = next(n for n in migration.body if isinstance(n, ast.FunctionDef) and n.name == "upgrade")
        found = {}
        for call in ast.walk(upgrade):
            if not isinstance(call, ast.Call) or not call.args:
                continue
            fn = call.func
            if isinstance(fn, ast.Name) and fn.id == "owned_table":
                table = ast.literal_eval(call.args[0])
                found[table] = {"id", "owner_id", "seed_key"} | {ast.literal_eval(c.args[0]) for c in call.args[1].elts}
            if isinstance(fn, ast.Attribute) and fn.attr == "create_table":
                table = ast.literal_eval(call.args[0])
                found[table] = {ast.literal_eval(c.args[0]) for c in call.args[1:] if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == "c"}
        self.assertEqual(found, expected)

    def test_no_destructive_or_import_ddl(self):
        for path in list((ROOT/"app").glob("*.py"))+list((ROOT/"agent").glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
            self.assertFalse(any(c.func.attr in ("create_all", "drop_all") for c in calls), path.name)
        self.assertNotIn("httpx", (ROOT/"app/bmi.py").read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
