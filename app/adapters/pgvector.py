
import logging

logger = logging.getLogger(__name__)


def is_pgvector_available() -> bool:
    """Check if pgvector extension is available in PostgreSQL"""
    # This will be checked when we try to use it
    # The actual check happens during vector search
    return True


async def vector_topk(vector: list[float], k: int) -> list[dict]:
    """
    Performs a vector search using pgvector to find the top-k most similar items.
    Uses cosine similarity search in PostgreSQL.
    """
    # Import pool dynamically to ensure it's initialized
    from app.adapters.pg import _pool, connect_db
    
    if _pool is None:
        logger.error("Database pool not initialized. Attempting to connect...")
        try:
            await connect_db()
            # Re-import after connection
            from app.adapters.pg import _pool as _pool_after
            if _pool_after is None:
                logger.error("Failed to initialize database pool after retry.")
                return []
            logger.info("Database pool initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return []
    
    # Use the pool
    from app.adapters.pg import _pool
    
    if not vector or len(vector) == 0:
        logger.warning("Empty query vector provided")
        return []
    
    try:
        # Convert vector to PostgreSQL array format
        # pgvector accepts vectors as PostgreSQL arrays which can be cast to vector type
        vector_list = [float(v) for v in vector]
        
        query = """
            SELECT 
                id,
                name,
                email,
                introduce,
                keywords,
                skills,
                cards,
                created_at,
                1 - (vector <=> $1::float[]::vector) as score
            FROM candidates
            WHERE vector IS NOT NULL
            ORDER BY vector <=> $1::float[]::vector
            LIMIT $2
        """
        
        async with _pool.acquire() as connection:
            # Pass Python list as PostgreSQL array, then cast to vector type
            # asyncpg handles the array parameter binding automatically
            rows = await connection.fetch(query, vector_list, k)
        
        # Convert results to list of dictionaries matching actual DB schema
        results = []
        for row in rows:
            result = {
                "id": str(row['id']),
                "score": float(row['score']) if row['score'] is not None else 0.0,
                "payload": {
                    "name": row.get('name'),
                    "email": row.get('email'),
                    "introduce": row.get('introduce'),
                    "keywords": row.get('keywords') if row.get('keywords') is not None else [],
                    "skills": row.get('skills') if row.get('skills') is not None else [],
                    "cards": row.get('cards') if row.get('cards') is not None else [],
                    "created_at": row.get('created_at').isoformat() if row.get('created_at') else None,
                }
            }
            results.append(result)
        
        logger.info(f"Vector search (pgvector) returned {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Vector search (pgvector) failed: {e}", exc_info=True)
        return []


async def retrieve_vectors(ids: list[str]) -> dict[str, list[float]]:
    """
    Retrieves vectors for a list of document IDs from PostgreSQL.
    """
    # Import pool dynamically to ensure it's initialized
    from app.adapters.pg import _pool, connect_db
    
    if _pool is None:
        logger.error("Database pool not initialized. Attempting to connect...")
        try:
            await connect_db()
            # Re-import after connection
            from app.adapters.pg import _pool as _pool_after
            if _pool_after is None:
                logger.error("Failed to initialize database pool after retry.")
                return {}
            logger.info("Database pool initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return {}
    
    # Use the pool
    from app.adapters.pg import _pool
    
    if not ids:
        return {}
    
    try:
        # Convert IDs to appropriate type (they might be integers or strings)
        # PostgreSQL candidates.id is SERIAL (integer), so we'll try integer first
        # Try to convert to integers
        id_list = []
        query = None
        
        try:
            id_list = [int(id_str) for id_str in ids]
            query = """
                SELECT id, vector
                FROM candidates
                WHERE id = ANY($1::int[])
                AND vector IS NOT NULL
            """
        except (ValueError, TypeError):
            # If conversion fails, try as text (might be TEXT ids in some schemas)
            id_list = [str(id_str) for id_str in ids]
            query = """
                SELECT id, vector
                FROM candidates
                WHERE id::text = ANY($1::text[])
                AND vector IS NOT NULL
            """
        
        async with _pool.acquire() as connection:
            rows = await connection.fetch(query, id_list)
        
        # Parse vector data from PostgreSQL
        # pgvector stores vectors as PostgreSQL arrays, which asyncpg returns as lists
        result_dict = {}
        for row in rows:
            vector_data = row['vector']
            if vector_data is not None:
                # asyncpg should return vector as a list of floats
                if isinstance(vector_data, list):
                    result_dict[str(row['id'])] = vector_data
                elif isinstance(vector_data, str):
                    # If it's a string, parse it
                    # Format: "[0.1, 0.2, ...]" or "{0.1, 0.2, ...}"
                    vector_str = vector_data.strip('[]{}')
                    result_dict[str(row['id'])] = [float(x.strip()) for x in vector_str.split(',')]
                else:
                    logger.warning(f"Unexpected vector type: {type(vector_data)}")
        
        logger.debug(f"Retrieved {len(result_dict)} vectors from PostgreSQL")
        return result_dict
        
    except Exception as e:
        logger.error(f"Vector retrieve (pgvector) failed: {e}", exc_info=True)
        return {}

