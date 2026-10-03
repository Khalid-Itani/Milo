"""Documentation-only OpenAPI generation without installed framework dependencies.

Parses actual request/response annotations. Runtime export_openapi.py is authoritative
and should replace this artifact once dependencies are installed. Never used by the app.
"""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ast.parse((ROOT/"app/schemas.py").read_text(encoding="utf-8"))
VISUALIZE = ast.parse((ROOT/"app/visualize.py").read_text(encoding="utf-8"))
CLASSES = {n.name: n for tree in (MODULE, VISUALIZE) for n in tree.body if isinstance(n, ast.ClassDef)}
ALIASES = {n.targets[0].id: n.value for n in MODULE.body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}

def name(node):
    return node.id if isinstance(node, ast.Name) else node.attr if isinstance(node, ast.Attribute) else ""

def schema(node):
    if isinstance(node, ast.Constant) and node.value is None:
        return {"type": "null"}
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return {"anyOf": [schema(node.left), schema(node.right)]}
    if isinstance(node, ast.Subscript):
        base = name(node.value)
        if base == "Annotated":
            parts = node.slice.elts
            out = schema(parts[0])
            for metadata in parts[1:]:
                if isinstance(metadata, ast.Call):
                    constraints(out, metadata)
            return out
        if base == "Literal":
            parts = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
            return {"type": "string", "enum": [ast.literal_eval(x) for x in parts]}
        if base == "list":
            return {"type": "array", "items": schema(node.slice)}
        if base == "dict":
            parts = node.slice.elts
            return {"type": "object", "additionalProperties": schema(parts[1])}
    key = name(node)
    if key in CLASSES:
        return {"$ref": "#/components/schemas/"+key}
    if key in ALIASES:
        return schema(ALIASES[key])
    return {"type": {"str": "string", "int": "integer", "float": "number", "bool": "boolean",
                     "dict": "object", "list": "array", "UUID": "string", "Date": "string", "AwareDatetime": "string"}.get(key, "object")} | (
        {"format": {"UUID": "uuid", "Date": "date", "AwareDatetime": "date-time"}[key]} if key in ("UUID", "Date", "AwareDatetime") else {})

def constraints(out, call):
    for kw in call.keywords:
        keys = {"gt": "exclusiveMinimum", "ge": "minimum", "lt": "exclusiveMaximum", "le": "maximum", "pattern": "pattern",
                "min_length": "minItems" if out.get("type") == "array" else "minLength",
                "max_length": "maxItems" if out.get("type") == "array" else "maxLength"}
        if kw.arg in keys:
            out[keys[kw.arg]] = ast.literal_eval(kw.value)

def fields(cls):
    inherited = {}
    for base in cls.bases:
        if name(base) in CLASSES:
            inherited.update(fields(CLASSES[name(base)]))
    for node in cls.body:
        if isinstance(node, ast.AnnAssign):
            inherited[node.target.id] = node
    return inherited

def class_schema(cls):
    properties, required = {}, []
    for key, node in fields(cls).items():
        out = schema(node.annotation)
        value = node.value
        has_default = value is not None
        if isinstance(value, ast.Call) and name(value.func) == "Field":
            constraints(out, value)
            kw = {k.arg: k.value for k in value.keywords}
            has_default = "default" in kw or "default_factory" in kw or bool(value.args)
        properties[key] = out
        if not has_default:
            required.append(key)
    result = {"type": "object", "properties": properties}
    if required:
        result["required"] = required
    if cls.name == "Input" or any(name(b) in ("Input", "Nutrition") for b in cls.bases):
        result["additionalProperties"] = False
    return result

def build():
    out = {"openapi": "3.1.0", "info": {"title": "Milo", "version": "2.0.0"},
           "x-verification": "Generated from source annotations without framework imports; runtime export not yet executed.",
           "paths": {}, "components": {"securitySchemes": {"HTTPBearer": {"type": "http", "scheme": "bearer"}},
                                      "schemas": {n: class_schema(c) for n, c in CLASSES.items()}}}
    tree = ast.parse((ROOT/"app/main.py").read_text(encoding="utf-8"))
    for fn in tree.body:
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in fn.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            method = decorator.func.attr
            if method not in ("get", "post", "patch", "delete") or not decorator.args:
                continue
            path = ast.literal_eval(decorator.args[0])
            response = next((schema(k.value) for k in decorator.keywords if k.arg == "response_model"), {})
            operation = {"operationId": fn.name+"_"+method, "responses": {"200": {
                "description": "Success", "content": {"application/json": {"schema": response}}}}}
            if path != "/health":
                operation["security"] = [{"HTTPBearer": []}]
                for code in ("401", "409", "422", "503"):
                    operation["responses"][code] = {"description": {"401": "Unauthorized", "409": "Conflict or profile incomplete",
                        "422": "Sanitized validation error", "503": "Service unavailable"}[code]}
            params = []
            for argument in fn.args.args:
                key, annotation = argument.arg, argument.annotation
                if key == "request":
                    continue
                if key == "body":
                    operation["requestBody"] = {"required": True, "content": {"application/json": {"schema": schema(annotation)}}}
                elif key == "key":
                    params.append({"name": "Idempotency-Key", "in": "header", "required": False,
                                   "schema": {"type": "string", "minLength": 1, "maxLength": 200}})
                else:
                    is_path = "{"+key+"}" in path
                    params.append({"name": key, "in": "path" if is_path else "query", "required": is_path, "schema": schema(annotation)})
            if params:
                operation["parameters"] = params
            out["paths"].setdefault(path, {})[method] = operation
    return out

if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
