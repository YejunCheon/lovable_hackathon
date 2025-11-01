
import logging
from app.adapters import pg, gemini

# 로거 생성 (명시적으로 로거 이름 지정)
logger = logging.getLogger(__name__)

async def generate_vectors_for_candidates():
    """
    Fetches candidates with NULL vectors, generates embeddings, and updates them in the DB.
    """
    try:
        # 1. Fetch candidates with NULL vectors
        rows = await pg.execute_query("SELECT id, name, introduce, keywords, skills, cards FROM candidates WHERE vector IS NULL")
        
        # Convert asyncpg Record objects to dictionaries
        candidates_to_update = [dict(row) for row in rows] if rows else []

        if not candidates_to_update:
            logger.info("No candidates found with NULL vectors. All vectors are up to date.")
            return {"message": "No candidates to update.", "count": 0}

        logger.info(f"Found {len(candidates_to_update)} candidates to process for vector generation.")

        for candidate in candidates_to_update:
            try:
                # 2. Combine text fields into a single document for embedding
                # We use COALESCE in the DB query, but as a fallback here, handle None safely.
                name = candidate.get('name', '') or ''
                introduce = candidate.get('introduce', '') or ''
                
                # Safely handle JSONB fields which might be None
                keywords = candidate.get('keywords', []) or []
                skills = candidate.get('skills', []) or []
                cards = candidate.get('cards', []) or []

                # Convert JSONB to a string representation for embedding
                keywords_text = ' '.join(map(str, keywords))
                skills_text = ' '.join(map(str, skills))
                cards_text = ' '.join(map(str, cards))

                document = f"Name: {name}\nIntroduction: {introduce}\nKeywords: {keywords_text}\nSkills: {skills_text}\nCards: {cards_text}"

                # 3. Generate vector embedding
                vector = await gemini.embed_query(document)

                # 4. Update the candidate's vector in the database
                await pg.execute_query(
                    "UPDATE candidates SET vector = $1 WHERE id = $2",
                    str(vector),
                    candidate['id']
                )
                logger.info(f"Successfully generated and updated vector for candidate ID: {candidate['id']}")

            except Exception as e:
                logger.error(f"Failed to process candidate ID {candidate.get('id', 'N/A')}: {e}")
        
        return {
            "message": f"Successfully generated vectors for {len(candidates_to_update)} candidates.",
            "count": len(candidates_to_update)
        }

    except Exception as e:
        logger.error(f"An error occurred during the vector generation process: {e}")
        # In a real app, you might want to raise an HTTPException here
        # to be handled by the API layer.
        raise
