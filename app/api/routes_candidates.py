
from fastapi import APIRouter, HTTPException
from app.services import candidates
import logging

router = APIRouter()

@router.post("/candidates/generate-vectors", tags=["Candidates"])
async def generate_vectors():
    """
    Triggers the generation of vector embeddings for candidates who don't have one yet.
    This is useful after a bulk import of candidate data.
    """
    try:
        result = await candidates.generate_vectors_for_candidates()
        return result
    except Exception as e:
        logging.error(f"Failed to trigger vector generation: {e}")
        raise HTTPException(status_code=500, detail="An internal error occurred during vector generation.")

