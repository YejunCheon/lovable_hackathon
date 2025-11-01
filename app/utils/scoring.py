from collections import defaultdict

def rrf_fusion(vec_results: list[dict], kw_results: list[dict], k: int = 60) -> list[dict]:
    """
    Reciprocal Rank Fusion (RRF) - Better blending method than weighted average.
    RRF combines rankings from multiple sources without requiring score normalization.
    
    Formula: score = 1 / (k + rank) for each list, then sum
    
    Args:
        vec_results: Vector search results
        kw_results: Keyword search results  
        k: RRF constant (typically 60)
    
    Returns:
        Blended results sorted by RRF score
    """
    # Normalize IDs to strings
    vec_ranks = {str(r['id']): i + 1 for i, r in enumerate(vec_results)}
    kw_ranks = {str(r['id']): i + 1 for i, r in enumerate(kw_results)}
    
    # Combine all document IDs
    all_ids = set(vec_ranks.keys()) | set(kw_ranks.keys())
    
    # Calculate RRF scores
    rrf_scores = {}
    for doc_id in all_ids:
        vec_rank = vec_ranks.get(doc_id)
        kw_rank = kw_ranks.get(doc_id)
        
        rrf_score = 0.0
        if vec_rank:
            rrf_score += 1.0 / (k + vec_rank)
        if kw_rank:
            rrf_score += 1.0 / (k + kw_rank)
        
        rrf_scores[doc_id] = rrf_score
    
    # Build result list
    blended_results = []
    for doc_id, rrf_score in rrf_scores.items():
        # Find the original document from either result list
        doc = next((r for r in vec_results if str(r['id']) == doc_id), None)
        if doc is None:
            doc = next((r for r in kw_results if str(r['id']) == doc_id), None)
        
        if doc:
            new_doc = doc.copy()
            new_doc['score'] = rrf_score
            blended_results.append(new_doc)
    
    # Sort by RRF score in descending order
    blended_results.sort(key=lambda x: x['score'], reverse=True)
    
    return blended_results


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