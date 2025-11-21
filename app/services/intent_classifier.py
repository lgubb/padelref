from openai import OpenAI
from app.core.prompts import PROMPT_INTENT_CLASSIFIER, SYSTEM_PROMPT
from app.core.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

async def classify_intent_llm(message: str) -> str:
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": PROMPT_INTENT_CLASSIFIER.replace("{{user_message}}", message)}
        ],
        max_tokens=10,
    )

    return completion.choices[0].message.content.strip()

