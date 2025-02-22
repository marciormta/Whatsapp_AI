import logging
import threading
from typing_extensions import Annotated

import uvicorn
from fastapi import FastAPI, Query, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.schema import Payload, Message, Audio, Image, User
from app.domain import message_service
from app.config import APP_PORT, VERIFICATION_TOKEN, ENVIRONMENT

IS_DEV_ENVIRONMENT = ENVIRONMENT == "development"

app = FastAPI(
    title="WhatsApp Bot",
    version="0.1.0",
    openapi_url="/openapi.json" if IS_DEV_ENVIRONMENT else None,
    docs_url="/docs" if IS_DEV_ENVIRONMENT else None,
    redoc_url="/redoc" if IS_DEV_ENVIRONMENT else None,
)

logger = logging.getLogger("uvicorn")


# Endpoint para verificação do webhook do WhatsApp
@app.get("/")
def verify_whatsapp(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: int = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFICATION_TOKEN:
        # Retorna somente o valor de hub_challenge como texto
        return str(hub_challenge)
    raise HTTPException(status_code=403, detail="Invalid verification token")


# Endpoints básicos de saúde
@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/readiness")
def readiness():
    return {"status": "ready"}


# Endpoint para configurar (atualizar) a URL de callback do webhook
webhook_config = {}

class WebhookConfig(BaseModel):
    callback_url: str

@app.post("/configure-webhook", status_code=200)
def configure_webhook(config: WebhookConfig):
    webhook_config["callback_url"] = config.callback_url
    logger.info(f"Webhook configured with callback URL: {config.callback_url}")
    return {"status": "Webhook configured", "callback_url": config.callback_url}


# Dependências para extrair informações do payload recebido do WhatsApp
def parse_message(payload: Payload) -> Message | None:
    if not payload.entry or not payload.entry[0].changes or not payload.entry[0].changes[0].value.messages:
        return None
    return payload.entry[0].changes[0].value.messages[0]

def get_current_user(message: Annotated[Message, Depends(parse_message)]) -> User | None:
    if not message:
        return None
    return message_service.authenticate_user_by_phone_number(message.from_)

def parse_audio_file(message: Annotated[Message, Depends(parse_message)]) -> Audio | None:
    if message and message.type == "audio":
        return message.audio
    return None

def parse_image_file(message: Annotated[Message, Depends(parse_message)]) -> Image | None:
    if message and message.type == "image":
        return message.image
    return None

def message_extractor(
    message: Annotated[Message, Depends(parse_message)],
    audio: Annotated[Audio, Depends(parse_audio_file)]
):
    if audio:
        return message_service.transcribe_audio(audio)
    if message and message.text:
        return message.text.body
    return None


# Endpoint para receber mensagens do WhatsApp
@app.post("/", status_code=200)
def receive_whatsapp(
    user: Annotated[User, Depends(get_current_user)],
    user_message: Annotated[str, Depends(message_extractor)],
    image: Annotated[Image, Depends(parse_image_file)] = None,
):
    if not user and not user_message and not image:
        return {"status": "ok"}

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if image:
        logger.info("Image received")
        return {"status": "Image received"}

    if user_message:
        logger.info(f"Received message from user {user.first_name} {user.last_name} ({user.phone}): {user_message}")
        # Se necessário, processe a mensagem em uma thread separada:
        # thread = threading.Thread(target=message_service.respond_and_send_message, args=(user_message, user))
        # thread.daemon = True
        # thread.start()
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=int(APP_PORT), reload=IS_DEV_ENVIRONMENT)
