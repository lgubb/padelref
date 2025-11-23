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


# -------------------------
# INTENTS : starters + mapping boutons
# -------------------------

INTENT_STARTERS = {
    "garantie": "Très bien, parlons garantie 👇\nPouvez-vous me donner la marque et le modèle du produit ?",
    "suivi_commande": "Bien sûr ! Pouvez-vous me donner votre numéro de commande ?",
    "retour_produit": "Pas de souci 👇\nQuel est le numéro de commande concerné ?",
    "conseil_produit": "Super ! Quel est votre niveau en padel (débutant, intermédiaire, avancé) ?"
}

INTENT_CLICK_MAP = {
    "INTENT_GARANTIE": "garantie",
    "INTENT_SUIVI": "suivi_commande",
    "INTENT_RETOUR": "retour_produit",
    "INTENT_CONSEIL": "conseil_produit",
}


# -------------------------
# FONCTION utilitaire : envoyer message Chatwoot
# -------------------------

async def send_to_chatwoot(account_id: int, conversation_id: int, body: dict):
    url = f"https://app.chatwoot.com/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"

    headers = {
        "api_access_token": CHATWOOT_API_TOKEN,
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(url, headers=headers, json=body)
        print(f"[Chatwoot] Status code: {response.status_code}")
        print(f"[Chatwoot] Response: {response.text}")
        return response


# -------------------------
# WEBHOOK PRINCIPAL
# -------------------------

@router.post("/webhook")
async def chatwoot_webhook(request: Request):
    payload = await request.json()
    print("📩 WEBHOOK REÇU :", payload)

    event = payload.get("event")

    # On traite uniquement les messages entrants
    if event != "message_created":
        print(f"⏭️ Event ignoré : {event}")
        return {"success": True}

    data = payload.get("conversation") or payload
    message_data = payload

    # Si ce n'est pas un message entrant → on ignore
    if message_data.get("message_type") != "incoming":
        print("⏭️ Message sortant ignoré")
        return {"success": True}

    user_message = message_data.get("content", "").strip()
    print(f"💬 Message utilisateur : {user_message}")

    account_id = payload["account"]["id"]
    conversation_id = data["id"]

    # -----------------------------------------------------
    # 1️⃣ Détection du PREMIER MESSAGE de la conversation
    # -----------------------------------------------------

    # Méthode Chatwoot fiable :
    # Le premier message n'a PAS de "in_reply_to"
    is_first_message = (
        message_data.get("content_attributes", {}).get("in_reply_to") is None
    )

    if is_first_message:
        print("🎯 Premier message détecté → envoi du menu d’intents")

        bot_answer = {
            "content_type": "input_select",
            "content": "Bonjour 👋\nSélectionnez une option ci-dessous ou posez une question libre :",
            "content_attributes": {
                "items": [
                    {"title": "🛡 Garantie", "value": "INTENT_GARANTIE"},
                    {"title": "📦 Suivi de commande", "value": "INTENT_SUIVI"},
                    {"title": "🔄 Retour produit", "value": "INTENT_RETOUR"},
                    {"title": "🎾 Conseil produit", "value": "INTENT_CONSEIL"},
                ]
            }
        }

        await send_to_chatwoot(account_id, conversation_id, bot_answer)
        return {"success": True}


    # -----------------------------------------------------
    # 2️⃣ Détection d’un CLIC SUR UN BOUTON
    # -----------------------------------------------------

    if user_message in INTENT_CLICK_MAP:
        intent_id = INTENT_CLICK_MAP[user_message]
        bot_answer = INTENT_STARTERS[intent_id]

        print(f"🎯 Intent cliqué : {intent_id}")
        print(f"↪️ Réponse : {bot_answer}")

        await send_to_chatwoot(account_id, conversation_id, {
            "content": bot_answer,
            "message_type": "outgoing",
            "private": False
        })

        return {"success": True}


    # -----------------------------------------------------
    # 3️⃣ COMPORTEMENT NORMAL → FAQ + Fallback (ton logique existante)
    # -----------------------------------------------------

    print("🤖 Traitement question libre")

    # 1. Keywords
    intent = match_intent_by_keywords(user_message, intents_map)
    print(f"🔍 Intent détecté (keywords) : {intent}")

    # 2. Classif LLM
    if not intent:
        intent = await classify_intent_llm(user_message)
        print(f"🤖 Intent détecté (LLM) : {intent}")

    # 3. FAQ
    faq_response = await get_faq_response(intent, user_message, faq_corpus)
    if faq_response:
        bot_answer = faq_response
    else:
        bot_answer = await fallback_answer(user_message)

    print(f"✉️ Réponse finale : {bot_answer}")

    await send_to_chatwoot(account_id, conversation_id, {
        "content": bot_answer,
        "message_type": "outgoing",
        "private": False
    })

    return {"success": True}
