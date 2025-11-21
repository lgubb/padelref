from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import httpx

from app.utils.loader import faq_corpus, intents_map
from app.services.keyword_matcher import match_intent_by_keywords
from app.services.intent_classifier import classify_intent_llm
from app.services.faq_responder import get_faq_response
from app.services.fallback import fallback_answer

router = APIRouter(prefix="/chatwoot", tags=["Chatwoot"])

@router.post("/webhook")
async def chatwoot_webhook(request: Request):

    payload = await request.json()
    print("📩 WEBHOOK REÇU :", payload)

    event = payload.get("event")
    data = payload.get("data", {})

    # -----------------------------------------
    # Ne traiter QUE les nouveaux messages client
    # -----------------------------------------
    if event != "message_created":
        return {"success": True}

    if data.get("message_type") != "incoming":
        return {"success": True}

    # -----------------------------------------
    # Récupération du texte utilisateur
    # -----------------------------------------
    user_message = data.get("content", "").strip()
    if not user_message:
        return {"success": True}

    # -----------------------------------------
    # Étape 1 : keywords
    # -----------------------------------------
    intent = match_intent_by_keywords(user_message, intents_map)

    # Étape 2 : fallback LLM si pas d’intent trouvé
    if not intent:
        intent = await classify_intent_llm(user_message)

    # Étape 3 : FAQ
    faq_response = await get_faq_response(intent, user_message, faq_corpus)
    if faq_response:
        bot_answer = faq_response
    else:
        # Étape 4 : fallback LLM
        bot_answer = await fallback_answer(user_message)

    # -----------------------------------------
    # Récupérer l'URL reply_to fournie par Chatwoot
    # -----------------------------------------
    reply_url = data["private"]["reply_to"]  # ⚠️ CRITIQUE
    print("➡️ reply_url =", reply_url)

    # -----------------------------------------
    # Envoyer la réponse à Chatwoot
    # -----------------------------------------
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(reply_url, json={"content": bot_answer})

    return {"success": True}
