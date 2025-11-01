
from app.adapters import gemini, qdrant, pg
from app.utils import scoring, mmr

async def hybrid_retrieve(persona: dict) -> list[dict]:
    """
    Orchestrates the hybrid retrieval process, including vector search, keyword search,
    score blending, and MMR for diversification.
    """
    query_text = persona.get("persona", {}).get("query_text", "")
    if not query_text:
        return []

    # 1. Get query embedding
    query_vector = await gemini.embed_query(query_text)

    # 2. Fetch from vector and keyword searches in parallel
    vec_results = await qdrant.vector_topk(query_vector, k=50)
    kw_results = await pg.db_keyword_topk(persona, k=50)

    # 3. Blend the scores
    # The PRD suggests alpha=0.6, but this can be tuned
    blended_results = scoring.blend_scores(vec_results, kw_results, alpha=0.6)

    # 4. Apply MMR for diversity
    # Retrieve vectors for the top blended results needed for MMR calculation
    top_ids_for_mmr = [doc['id'] for doc in blended_results[:20]] # Use top 20 for MMR
    if not top_ids_for_mmr:
        return []
        
    doc_vectors = await qdrant.retrieve_vectors(top_ids_for_mmr)
    
    # The PRD suggests k=12 for the final diverse set
    diverse_results = mmr.mmr(blended_results[:20], doc_vectors, lambda_val=0.5, k=12)

    return diverse_results
