from typing import List

from app.adapters.pg import execute_query


async def search_profile_with_vectors(vectors: List[List[float]]) -> List[str]:
    vector_search_sum_equation = ", ".join([f"(vector <-> '{vector}'::vector)" for vector in vectors])
    query = f"""
    WITH vector_search AS (
        SELECT LEAST({vector_search_sum_equation}) AS distance, text FROM text_embeddings
    ),
    searched_candidate AS (
        SELECT candidate_id, min(distance) as distance_min FROM candidate_embedding_word_map
        INNER JOIN vector_search ON candidate_embedding_word_map.text = vector_search.text
        GROUP BY candidate_id
    )
    SELECT candidate_id FROM searched_candidate ORDER BY distance_min LIMIT 10
    """
    
    with open("query.sql", "w") as f:
        f.write(query)

    result = await execute_query(query)
    return [ row['candidate_id'] for row in result ]
