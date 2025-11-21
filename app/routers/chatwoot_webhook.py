from fastapi import APIRouter, Request
import httpx
import os

from app.utils.loader import faq_corpus, intents_map
from app.services.keyword_matcher import match_intent_by_keywords
from app.services.intent_classifier import classify_intent_llm
from app.services.faq_responder import get_faq_response
from app.services.fallback import fallback_answer

router = APIRouter(prefix="/chatwoot", tags=["Chatwoot"])

CHATWOOT_API_TOKEN = os.getenv("CHATWOOT_API_TOKEN")

@router.post("/webhook")
async def chatwoot_webhook(request: Request):
    payload = await request.json()
    print("📩 WEBHOOK REÇU :", payload)

    event = payload.get("event")

    # On traite uniquement les messages entrants
    if event != "message_created":
        print(f"⏭️ Event ignoré : {event}")
        return {"success": True}

    data = payload.get("conversation") or payload  # 🔧 Fix structure
    message_data = payload  # Le message lui-même

    if message_data.get("message_type") != "incoming":
        print(f"⏭️ Message sortant ignoré")
        return {"success": True}

    user_message = message_data.get("content", "").strip()
    if not user_message:
        print("⚠️ Message vide")
        return {"success": True}

    print(f"💬 Message utilisateur : {user_message}")

    # 1. Keywords
    intent = match_intent_by_keywords(user_message, intents_map)
    print(f"🔍 Intent détecté (keywords) : {intent}")

    # 2. Fallback LLM
    if not intent:
        intent = await classify_intent_llm(user_message)
        print(f"🤖 Intent détecté (LLM) : {intent}")

    # 3. Réponse FAQ
    faq_response = await get_faq_response(intent, user_message, faq_corpus)
    if faq_response:
        bot_answer = faq_response
    else:
        bot_answer = await fallback_answer(user_message)

    print(f"✅ Réponse générée : {bot_answer}")

    # -----------------------------
    # ENVOI DE LA RÉPONSE A CHATWOOT
    # -----------------------------
    account_id = payload["account"]["id"]
    conversation_id = data["id"]

    print(f"📤 Envoi vers Chatwoot - Account: {account_id}, Conversation: {conversation_id}")

    # 🚨 VÉRIFICATION CRITIQUE
    if not CHATWOOT_API_TOKEN:
        print("❌ ERREUR : CHATWOOT_API_KEY non définie !")
        return {"success": False, "error": "Missing API key"}

    url = f"https://app.chatwoot.com/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"

    headers = {
        "api_access_token": CHATWOOT_API_TOKEN,  # 🔧 Fix : utilise "api_access_token" au lieu de "Authorization"
        "Content-Type": "application/json"
    }

    body = {
        "content": bot_answer,
        "message_type": "outgoing",
        "private": False  # 🔧 Important : message visible dans le chat
    }

    print(f"🌐 URL : {url}")
    print(f"📦 Body : {body}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=body)

            print(f"📡 Status Code : {response.status_code}")
            print(f"📄 Réponse Chatwoot : {response.text}")

            if response.status_code == 200:
                print("✅ Message envoyé avec succès à Chatwoot")
                return {"success": True}
            else:
                print(f"❌ ERREUR Chatwoot : {response.status_code} - {response.text}")
                return {"success": False, "error": response.text}

    except Exception as e:
        print(f"💥 EXCEPTION lors de l'envoi : {str(e)}")
        return {"success": False, "error": str(e)}
