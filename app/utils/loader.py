import json
from pathlib import Path

BASE_PATH = Path(__file__).resolve().parents[2] / "app" / "data"

def load_json(filename: str):
    with open(BASE_PATH / filename, "r", encoding="utf-8") as f:
        return json.load(f)

faq_corpus = load_json("faq_corpus.json")
intents_map = load_json("intents.json")
