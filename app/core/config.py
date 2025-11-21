import os

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY n'est pas défini dans l'environnement.")

CHATWOOT_API_TOKEN = os.getenv("CHATWOOT_API_TOKEN")
if not CHATWOOT_API_TOKEN:
    raise ValueError("CHATWOOT_API_TOKEN n'est pas défini dans l'environnement.")

CHATWOOT_BASE_URL = os.getenv("CHATWOOT_BASE_URL")

CHATWOOT_INBOX_ID = os.getenv("CHATWOOT_INBOX_ID")
