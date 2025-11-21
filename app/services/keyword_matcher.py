import re
import unicodedata

# Normalisation texte
def normalize(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = text.encode("ascii", "ignore").decode("utf-8")
    return text

def match_intent_by_keywords(message: str, intents_map: dict) -> str | None:
    msg = normalize(message)

    for intent, data in intents_map.items():
        for kw in data["keywords"]:
            pattern = r"\b" + re.escape(normalize(kw)) + r"(s)?\b"
            if re.search(pattern, msg):
                return intent

    return None
