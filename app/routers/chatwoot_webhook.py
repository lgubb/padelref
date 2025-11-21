from fastapi import APIRouter, Request
import httpx
import os

from app.utils.loader import faq_corpus, intents_map
from app.services.keyword_matcher import match_intent_by_keywords
from app.services.intent_classifier import classify_intent_llm
from app.services.faq_responder import get_faq_response
from app.services.fallback import fallback_answer

router = APIRouter(prefix="/chatwoot", tags=["Chatwoot"])

CHATWOOT_API_KEY = os.getenv("CHATWOOT_API_KEY")  # 🚨 DOIT être dans Render

@router.post("/webhook")
async def chatwoot_webhook(request: Request):

    payload = await request.json()
    print("📩 WEBHOOK REÇU :", payload)

    event = payload.get("event")
    data = payload.get("data", {})

    # On traite uniquement les messages entrants
    if event != "message_created":
        return {"success": True}

    if data.get("message_type") != "incoming":
        return {"success": True}

    user_message = data.get("content", "").strip()
    if not user_message:
        return {"success": True}

    # 1. Keywords
    intent = match_intent_by_keywords(user_message, intents_map)

    # 2. Fallback LLM
    if not intent:
        intent = await classify_intent_llm(user_message)

    # 3. Réponse FAQ
    faq_response = await get_faq_response(intent, user_message, faq_corpus)
    if faq_response:
        bot_answer = faq_response
    else:
        bot_answer = await fallback_answer(user_message)

    # -----------------------------
    # ENVOI DE LA RÉPONSE A CHATWOOT
    # -----------------------------
    account_id = payload["account"]["id"]
    conversation_id = data["conversation"]["id"]

    url = f"https://app.chatwoot.com/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"

    headers = {
        "Authorization": f"Bearer {CHATWOOT_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        await client.post(url, headers=headers, json={
            "content": bot_answer,
            "message_type": "outgoing"
        })

    return {"success": True}
