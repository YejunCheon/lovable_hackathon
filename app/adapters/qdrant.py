
from qdrant_client import QdrantClient, models
from app.core.config import settings

# Initialize Qdrant client
qdrant_client = QdrantClient(
    url=settings.QDRANT_URL, 
    api_key=settings.QDRANT_API_KEY,
    timeout=60, # Set a higher timeout
)

async def vector_topk(vector: list[float], k: int) -> list[dict]:
    """
    Performs a vector search in Qdrant to find the top-k most similar items.
    """
    search_result = qdrant_client.search(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query_vector=vector,
        limit=k,
        with_payload=True, # Include payload in the result
        with_vectors=False # Do not include vectors in the result
    )
    
    # Convert search results to a list of dictionaries
    results = [
        {
            "id": point.id,
            "score": point.score,
            "payload": point.payload
        }
        for point in search_result
    ]
    
    return results

async def retrieve_vectors(ids: list[str]) -> dict[str, list[float]]:
    """
    Retrieves vectors for a list of document IDs from Qdrant.
    """
    records = qdrant_client.retrieve(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        ids=ids,
        with_vectors=True,
        with_payload=False
    )
    
    return {record.id: record.vector for record in records}
