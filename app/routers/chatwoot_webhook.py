from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import httpx
import os

from app.utils.loader import faq_corpus, intents_map
from app.services.keyword_matcher import match_intent_by_keywords
from app.services.intent_classifier import classify_intent_llm
from app.services.faq_responder import get_faq_response
from app.services.fallback import fallback_answer

router = APIRouter(prefix="/chatwoot", tags=["Chatwoot"])

CHATWOOT_API_KEY = os.getenv("CHATWOOT_API_KEY")
CHATWOOT_BASE_URL = "https://app.chatwoot.com"  # si tu utilises chatwoot cloud


@router.post("/webhook")
async def chatwoot_webhook(request: Request):

    payload = await request.json()
    print("📩 WEBHOOK REÇU :", payload)

    event = payload.get("event")
    data = payload.get("data", {})

    # Ne répondre qu'aux messages entrants du client
    if event != "message_created":
        return {"success": True}

    if data.get("message_type") != "incoming":
        return {"success": True}

    user_message = data.get("content", "").strip()
    if not user_message:
        return {"success": True}

    # INTENT + FAQ + FALLBACK
    intent = match_intent_by_keywords(user_message, intents_map)
    if not intent:
        intent = await classify_intent_llm(user_message)

    faq_response = await get_faq_response(intent, user_message, faq_corpus)
    bot_answer = faq_response or await fallback_answer(user_message)

    # ---------- Récupération account_id + conversation_id ----------
    account_id = payload["data"]["account_id"]
    conversation_id = payload["data"]["conversation_id"]

    # ---------- URL de réponse ----------
    url = f"{CHATWOOT_BASE_URL}/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"

    headers = {
        "Content-Type": "application/json",
        "api_access_token": CHATWOOT_API_KEY
    }

    # ---------- Envoi à Chatwoot ----------
    async with httpx.AsyncClient() as client:
        r = await client.post(url, headers=headers, json={
            "content": bot_answer,
            "message_type": "outgoing",
            "private": False
        })
        print("➡️ REPONSE CHATWOOT :", r.status_code, r.text)

    return {"success": True}
