
import math

def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculates cosine similarity between two vectors."""
    dot_product = sum(p*q for p,q in zip(vec1, vec2))
    magnitude = math.sqrt(sum([val**2 for val in vec1])) * math.sqrt(sum([val**2 for val in vec2]))
    if not magnitude:
        return 0
    return dot_product / magnitude

def mmr(documents: list[dict], vectors: dict[str, list[float]], lambda_val: float, k: int) -> list[dict]:
    """
    Performs Maximal Marginal Relevance (MMR) to diversify the result set.
    `documents` is the list of candidate documents, sorted by relevance.
    `vectors` is a dictionary mapping document ID to its vector.
    `lambda_val` controls the trade-off between relevance and diversity.
    `k` is the number of results to return.
    """
    if not documents or not vectors:
        return []

    # Ensure we have vectors for all documents
    doc_ids_with_vectors = [doc['id'] for doc in documents if doc['id'] in vectors]
    if not doc_ids_with_vectors:
        return documents[:k] # Return top k if no vectors are available

    # Normalize relevance scores (original scores from blended search)
    scores = {doc['id']: doc['score'] for doc in documents}
    max_score = max(scores.values()) if scores else 0
    if max_score > 0:
        for doc_id in scores:
            scores[doc_id] /= max_score

    selected_ids = []
    remaining_ids = doc_ids_with_vectors.copy()

    # Greedily select the first document (most relevant)
    if remaining_ids:
        first_id = remaining_ids.pop(0)
        selected_ids.append(first_id)

    while len(selected_ids) < k and remaining_ids:
        mmr_scores = {}
        for doc_id in remaining_ids:
            relevance = scores.get(doc_id, 0)
            
            # Calculate similarity with already selected documents
            max_sim = 0
            if selected_ids:
                sims = [cosine_similarity(vectors[doc_id], vectors[sel_id]) for sel_id in selected_ids]
                if sims:
                    max_sim = max(sims)
            
            mmr_score = lambda_val * relevance - (1 - lambda_val) * max_sim
            mmr_scores[doc_id] = mmr_score
        
        if not mmr_scores:
            break

        # Select the document with the highest MMR score
        best_id = max(mmr_scores, key=mmr_scores.get)
        selected_ids.append(best_id)
        remaining_ids.remove(best_id)

    # Return the selected documents in the order they were selected
    final_documents = [doc for doc in documents if doc['id'] in selected_ids]
    final_documents.sort(key=lambda doc: selected_ids.index(doc['id']))
    
    return final_documents
