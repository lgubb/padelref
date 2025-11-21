from app.core.prompts import PROMPT_FAQ
from openai import OpenAI
from app.core.config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

async def get_faq_response(intent: str, message: str, faq_corpus: dict):
    entries = faq_corpus.get(intent, [])

    if not entries:
        return None

    prompt_faq = PROMPT_FAQ \
        .replace("{{faq_entries}}", str(entries)) \
        .replace("{{user_message}}", message)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt_faq}
        ]
    )

    return completion.choices[0].message.content.strip()

