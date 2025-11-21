from fastapi import APIRouter, HTTPException
from app.utils.loader import faq_corpus, intents_map
from app.services.keyword_matcher import match_intent_by_keywords
from app.services.intent_classifier import classify_intent_llm
from app.services.faq_responder import get_faq_response
from app.services.fallback import fallback_answer
from app.utils.logger import log_message

router = APIRouter(prefix="/tiledesk", tags=["chatbot"])

@router.post("/message")
async def tiledesk_message(payload: dict):

    # Sécuriser : vérifier qu'on reçoit bien un message
    if not payload:
        raise HTTPException(status_code=400, detail="Payload vide")

    # Récupération robuste des messages Tiledesk
    user_message = (
        payload.get("text")
        or payload.get("message")
        or payload.get("last_message")
        or ""
    ).strip()

    if not user_message:
        return {"text": "Je n'ai pas reçu de message. Pouvez-vous reformuler ?"}

    log_message(f"[USER] {user_message}")

    # 1. Keywords matcher
    intent = match_intent_by_keywords(user_message, intents_map)

    # 2. Intent classifier si aucun keyword match
    if not intent:
        intent = await classify_intent_llm(user_message)
        log_message(f"[INTENT LLM] {intent}")

    # 3. Recherche FAQ
    faq_response = await get_faq_response(intent, user_message, faq_corpus)

    if faq_response:
        log_message(f"[BOT-FAQ] {faq_response}")
        return {"text": faq_response}

    # 4. Fallback si aucune réponse
    fb = await fallback_answer(user_message)
    log_message(f"[BOT-FALLBACK] {fb}")

    return {"text": fb}
