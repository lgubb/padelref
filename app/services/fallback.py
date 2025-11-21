from app.core.prompts import PROMPT_FALLBACK
from openai import OpenAI
from app.core.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

async def fallback_answer(message: str):
    prompt = PROMPT_FALLBACK.replace("{{user_message}}", message)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return completion.choices[0].message.content.strip()

