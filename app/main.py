from fastapi import FastAPI
from app.routers import chatbot
from app.routers import chatwoot_webhook
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.include_router(chatbot.router)
app.include_router(chatwoot_webhook.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}
