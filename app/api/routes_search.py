from fastapi import APIRouter, HTTPException
from app.schemas.search import SearchRequest
from app.schemas.persona import PersonaResponse
from app.services.persona import build_persona
import logging

router = APIRouter()

@router.post("/search", response_model=PersonaResponse)
async def search(req: SearchRequest) -> PersonaResponse:
    """
    Accepts a search query and returns a structured Persona object.
    """
    try:
        persona_response = await build_persona(req)
        return persona_response
    except Exception as e:
        logging.error(f"Error during persona generation: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate persona.")