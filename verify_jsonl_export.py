import json

from services.exporter import export_news

path = export_news("jsonl")
lines = path.read_text(encoding="utf-8").splitlines()
objects = [json.loads(line) for line in lines]
assert path.name == "news.jsonl"
assert all(isinstance(obj, dict) for obj in objects)
print(f"ok: {path} ({len(objects)}건)")
