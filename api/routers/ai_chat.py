from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.deps import get_current_user_optional, get_db
from db.models.user import User
from sqlalchemy.orm import Session
from db.models.product import Product
import json

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    response: str

@router.post("/", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_optional)
) -> Any:
    """
    Endpoint para chatear con el Personal Shopper IA.
    """
    from core.config import settings
    from google import genai
    
    products = db.query(Product).limit(50).all()
    catalog_context = "Catálogo de productos disponibles:\n"
    for p in products:
        cat = p.category.name if p.category else "Otros"
        catalog_context += f"- {p.name} ({cat}): ${p.base_price}. {p.description or ''}\n"

    system_instruction = (
        "Eres un Personal Shopper experto en moda para FashionStore. "
        "Tu objetivo es ayudar al usuario a encontrar la ropa perfecta de nuestro catálogo. "
        "Sé amable, persuasivo y da consejos de estilo. "
        "Usa emojis. Mantén tus respuestas concisas.\n\n"
        f"{catalog_context}"
    )

    try:
        # Usar la clave gratuita para el chatbot
        api_key = getattr(settings, 'GEMINI_API_KEY_2', getattr(settings, 'GEMINI_API_KEY_1', ''))
        client = genai.Client(api_key=api_key)
        
        conversation = ""
        for msg in request.messages:
            conversation += f"{msg.role}: {msg.content}\n"
        
        prompt = f"{system_instruction}\n\nHistorial de chat:\n{conversation}\nAI:"
        
        response = client.models.generate_content(
            model="gemini-1.5-flash",  # Modelo gratuito de texto
            contents=prompt,
        )
        
        if not response.text:
            raise ValueError("Respuesta vacía de Gemini")
            
        return ChatResponse(response=response.text.strip())
    except Exception as e:
        print(f"Error en AI Chat: {e}")
        raise HTTPException(status_code=500, detail="Error al comunicarse con el asistente IA.")
