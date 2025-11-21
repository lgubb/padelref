📘 README — Architecture & Pipeline du Chatbot PadelReference (Phase 1)
🧩 Objectif du projet

Développer un backend FastAPI relié à un widget Tiledesk permettant :

de répondre automatiquement aux questions fréquentes du SAV

d’identifier les intentions utilisateur (« intents »)

d’extraire des réponses depuis un corpus de FAQ

d’utiliser l’IA uniquement lorsque nécessaire

d’envoyer une réponse claire et fiable au chatbot

Phase 1 = Réduction de 30–40% du SAV sur les questions “poubelles”.

🏗️ Architecture du projet
padelref/
│
├── app/
│   ├── main.py
│   ├── routers/
│   │     └── chatbot.py
│   ├── services/
│   │     ├── keyword_matcher.py
│   │     ├── intent_classifier.py
│   │     ├── faq_responder.py
│   │     └── fallback.py
│   ├── core/
│   │     ├── config.py
│   │     └── prompts.py
│   ├── utils/
│   │     ├── loader.py
│   │     └── logger.py
│   └── data/
│         ├── faq_corpus.json
│         └── intents.json
│
├── requirements.txt
├── .envrc
└── README.md

📂 Rôle de chaque fichier
1) main.py

Point d’entrée FastAPI.

Installe le routeur principal (/tiledesk/message).

Ajoute CORS + healthcheck.

➡️ C’est la porte du backend.

2) routers/chatbot.py

Le cerveau du pipeline.

Il gère :

la réception du message venant de Tiledesk

l’extraction du message utilisateur

l’appel successif de :

keyword matcher

intent classifier (LLM)

FAQ responder (LLM)

fallback (LLM)

l’envoi de la réponse finale à Tiledesk

➡️ C’est ici que tout s’enchaîne.

3) services/keyword_matcher.py

Outil rapide pour détecter un intent via mots-clés.

Exemples :

"livraison", "expédition" → intent = livraison

"garantie", "cassée", "fissure" → intent = garantie

➡️ Solution rapide, non IA, qui couvre 80% des cas.

4) services/intent_classifier.py

Si le keyword matcher ne trouve rien :

👉 on appelle l’IA (GPT-4o-mini)
pour classifier le message parmi les intents :

livraison

commande

garantie

retour_colis

produits

paiement

fallback
etc.

Le LLM reçoit le PROMPT_INTENT_CLASSIFIER, et retourne un seul mot : le nom de l’intent.

➡️ IA utilisée uniquement pour: classification sémantique fine.

5) services/faq_responder.py

Une fois l’intent identifié :

on récupère les questions/réponses associées dans faq_corpus.json

on envoie un message à l’IA pour qu’elle sélectionne la réponse la plus adaptée
→ avec seulement les infos du corpus
→ sans inventer ni halluciner

➡️ L’IA ne génère pas du contenu libre → elle choisit parmi un corpus.

6) services/fallback.py

Si :

pas d’intent fiable

pas de réponse dans la FAQ

message hors scope

Alors :
👉 l’IA génère une réponse courte, neutre, utile
👉 invite à reformuler ou à contacter le support
👉 sans halluciner

➡️ C’est une sécurité.

7) core/prompts.py

Contient tous les prompts système :

SYSTEM_PROMPT

PROMPT_INTENT_CLASSIFIER

PROMPT_FAQ

PROMPT_FALLBACK

➡️ C’est la personnalité et la stratégie de l’assistant.

8) core/config.py

Charge les variables d’environnement depuis .envrc (direnv).

➡️ Sécurise la clé OpenAI.

9) utils/loader.py

Charge les fichiers JSON au démarrage :

faq_corpus.json

intents.json

➡️ Centralise les données du bot.

10) utils/logger.py

Écrit dans logs.txt :

message utilisateur

intent détecté

réponse envoyée

➡️ Très utile pour débug et analytics.

11) data/faq_corpus.json

FAQ structurée par catégories.

Exemple :
"livraison": [
  { "q": "...", "a": "..." }
]
➡️ Source de vérité.

12) data/intents.json

Définition des intents + mots-clés associés.

➡️ Pour le routing rapide non-IA.

🔥 COMMENT LE PIPELINE FONCTIONNE EXACTEMENT
🔄 Étape 0 : Tiledesk → webhook → FastAPI

Le message arrive sous forme :

{
  "text": "Où est mon colis ?"
}

Lien webhook :

POST /tiledesk/message

🔄 Étape 1 : Extraction du message

chatbot.py récupère :

user_message = payload.get("text") or ...

🔄 Étape 2 : Keyword matching (rapide, non IA)

Ex :

"colis"

"livraison"

→ match immédiat → intent = livraison

Si pas de match, on va à l’étape suivante.

🔄 Étape 3 : Intent classifier IA (GPT-4o-mini)

Le LLM reçoit :
"Voici la liste des intents... Donne 1 intent pour : 'J’ai cassé ma raquette'"

Il répond :
garantie

➡️ L’IA intervient ici uniquement si le matcher a échoué.

🔄 Étape 4 : FAQ responder IA (GPT-4o-mini)

On envoie au modèle :

la liste des (q,a) du bon intent

le message utilisateur

Et il doit sélectionner la bonne réponse, sans inventer.

➡️ L’IA intervient ici pour générer la réponse finale, mais en utilisant uniquement le contenu du JSON.

🔄 Étape 5 : Fallback IA (si aucune réponse trouvée)

L’IA rédige :

“Je ne trouve pas encore cette information, pouvez-vous préciser votre demande ?”

➡️ L’IA intervient ici comme filet de sécurité.

🔄 Étape 6 : Envoi au frontend Tiledesk

FastAPI renvoie :
{
  "text": "Vous pouvez suivre votre colis grâce au lien reçu dans l’email d’expédition."
}

Tiledesk l’affiche dans le widget.

🎯 Résumé clair : quand intervient l’IA ?
Étape	IA utilisée ?	Rôle
Keywords matcher	❌ Non	Ultra rapide, regex
Intent classifier	✅ Oui	Comprendre l’intention
FAQ responder	✅ Oui	Choisir la meilleure réponse parmi JSON
Fallback	✅ Oui	Réponse neutre et polie
Envoi réponse	❌ Non	Simple routage


🚀 Conclusion : Vue d’ensemble

Ton backend Phase 1 :

reçoit un message

identifie l’intent

sélectionne la réponse la plus pertinente dans la FAQ

utilise l’IA uniquement si nécessaire

renvoie une réponse propre, courte, professionnelle

prépare le terrain pour les phases 2 / 3 (garantie & retours)

sera compatible Phase 4 (RAG produit)

Tu as maintenant une architecture professionnelle, claire, et scalable.
