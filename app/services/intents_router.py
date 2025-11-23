# app/services/intents_router.py

from typing import Dict

INTENT_STARTERS: Dict[str, str] = {
    "garantie": "Très bien, parlons garantie 👇\nPouvez-vous me donner la marque et le modèle du produit ?",
    "suivi_commande": "Je m’en occupe ! Pouvez-vous me donner votre numéro de commande ?",
    "retour_produit": "Pas de souci, je vous aide pour un retour 👇\nQuel est le numéro de commande concerné ?",
    "conseil_produit": "Super ! Quel type de produit recherchez-vous ? "
}

def get_starter_for_intent(intent_id: str) -> str:
    """Renvoie la phrase de démarrage pour un intent."""
    return INTENT_STARTERS.get(intent_id.lower(), "Je n’ai pas compris l’intent demandé.")
