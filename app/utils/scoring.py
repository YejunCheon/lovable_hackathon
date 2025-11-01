from collections import defaultdict

def blend_scores(vec_results: list[dict], kw_results: list[dict], alpha: float) -> list[dict]:
    """
    Blends scores from vector search and keyword search using a weighted average.
    Vector search scores are normalized, and keyword search ranks are converted to scores using reciprocal rank.
    
    Note: ID types may differ (str vs int), so we normalize them to strings for comparison.
    """
    
    # Normalize IDs to strings for consistent comparison
    # Vector results may have string IDs, keyword results may have int IDs
    vec_scores = {str(r['id']): r['score'] for r in vec_results}
    if vec_scores:
        max_vec_score = max(vec_scores.values())
        if max_vec_score > 0:
            for doc_id in vec_scores:
                vec_scores[doc_id] /= max_vec_score

    # Convert keyword ranks to scores using reciprocal rank, as they are ordered by relevance.
    kw_scores = {str(r['id']): 1.0 / (i + 1) for i, r in enumerate(kw_results)}

    # Combine results
    all_ids = set(vec_scores.keys()) | set(kw_scores.keys())
    
    blended_results = []
    for doc_id in all_ids:
        vec_score = vec_scores.get(doc_id, 0)
        kw_score = kw_scores.get(doc_id, 0)
        
        blended_score = alpha * vec_score + (1 - alpha) * kw_score
        
        # Find the original document from either result list to retain its payload
        # Compare with normalized string IDs
        doc = next((r for r in vec_results if str(r['id']) == doc_id), None)
        if doc is None:
            doc = next((r for r in kw_results if str(r['id']) == doc_id), None)
        
        if doc:
            # Create a new dict to avoid modifying the original
            new_doc = doc.copy()
            new_doc['score'] = blended_score
            blended_results.append(new_doc)

    # Sort by blended score in descending order
    blended_results.sort(key=lambda x: x['score'], reverse=True)
    
    return blended_results