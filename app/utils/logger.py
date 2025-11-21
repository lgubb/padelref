from datetime import datetime

def log_message(text: str):
    with open("logs.txt", "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {text}\n")
