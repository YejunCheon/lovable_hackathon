import asyncpg
from app.core.config import settings
import logging
import ssl

_pool = None

async def connect_db():
    """
    Initializes the PostgreSQL connection pool.
    """
    global _pool
    if _pool is not None and not _pool.is_closing():
        # Pool is already active, do nothing
        return

    # If pool is None or closed, create a new one
    try:
        # Supabase requires SSL connection
        # Create SSL context for Supabase (verify mode is CERT_NONE for Supabase's self-signed certs)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        _pool = await asyncpg.create_pool(
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            ssl=ssl_context,  # Supabase requires SSL
            min_size=1,
            max_size=10,
            command_timeout=60
        )
        logging.info(f"PostgreSQL connection pool created successfully. Connected to {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
    except Exception as e:
        logging.error(f"Failed to create PostgreSQL connection pool: {e}")
        logging.error(f"Connection details: host={settings.DB_HOST}, port={settings.DB_PORT}, database={settings.DB_NAME}, user={settings.DB_USER}")
        raise

async def close_db():
    """
    Closes the PostgreSQL connection pool.
    """
    global _pool
    if _pool:
        await _pool.close()
        logging.info("PostgreSQL connection pool closed.")

async def execute_query(query: str, *args):
    """
    Executes a SQL query and returns the results.
    """
    if _pool is None:
        raise ConnectionError("Database pool not initialized. Call connect_db() first.")
    
    async with _pool.acquire() as connection:
        try:
            return await connection.fetch(query, *args)
        except Exception as e:
            logging.error(f"Query execution failed: {e}")
            logging.error(f"Query: {query}")
            logging.error(f"Args: {args}")
            raise

async def fetch_val(query: str, *args):
    """
    Executes a SQL query and returns a single value.
    """
    if _pool is None:
        raise ConnectionError("Database pool not initialized. Call connect_db() first.")
    
    async with _pool.acquire() as connection:
        return await connection.fetchval(query, *args)

async def structured_search(search_filters: dict, k: int = 30) -> list[dict]:
    """
    Performs structured search using field-specific WHERE conditions.
    Uses JSONB operators for precise matching.
    
    Conditions are connected with OR to maximize candidate pool.
    Each field's conditions are grouped, and all field groups are OR'd together.
    
    Args:
        search_filters: Dictionary with field-specific filters
        k: Maximum number of results to return
    
    Returns:
        List of candidate dictionaries with 'score' field
    """
    if _pool is None:
        raise ConnectionError("Database pool not initialized. Call connect_db() first.")
    
    # Calculate total number of terms for normalization
    total_terms = 0
    if search_filters.get('keywords_any'):
        total_terms += len(search_filters['keywords_any'])
    if search_filters.get('skills_any'):
        total_terms += len(search_filters['skills_any'])
    
    # Build field-specific condition groups (each group uses OR internally)
    field_groups = []
    params = []
    param_idx = 1
    
    # keywords filtering (JSONB array) - OR within field
    keyword_conditions = []
    if search_filters.get('keywords_any'):
        keywords_list = search_filters['keywords_any']
        keyword_conditions.append(f"keywords ?| ${param_idx}::text[]")
        params.append(keywords_list)
        param_idx += 1
    
    if search_filters.get('keywords_all'):
        keywords_all = search_filters['keywords_all']
        keyword_conditions.append(f"keywords ?& ${param_idx}::text[]")
        params.append(keywords_all)
        param_idx += 1
    
    if keyword_conditions:
        field_groups.append(f"({' OR '.join(keyword_conditions)})")
    
    # skills filtering (JSONB array) - OR within field
    skill_conditions = []
    if search_filters.get('skills_any'):
        skills_list = search_filters['skills_any']
        skill_conditions.append(f"skills ?| ${param_idx}::text[]")
        params.append(skills_list)
        param_idx += 1
    
    if search_filters.get('skills_all'):
        skills_all = search_filters['skills_all']
        skill_conditions.append(f"skills ?& ${param_idx}::text[]")
        params.append(skills_all)
        param_idx += 1
    
    if skill_conditions:
        field_groups.append(f"({' OR '.join(skill_conditions)})")
    
    # name filtering (TEXT) - already OR'd internally
    if search_filters.get('name_contains'):
        name_terms = search_filters['name_contains']
        name_conditions = []
        for term in name_terms:
            name_conditions.append(f"name ILIKE ${param_idx}")
            params.append(f"%{term}%")
            param_idx += 1
        if name_conditions:
            field_groups.append(f"({' OR '.join(name_conditions)})")
    
    # introduce filtering (TEXT) - already OR'd internally
    if search_filters.get('introduce_contains'):
        intro_terms = search_filters['introduce_contains']
        intro_conditions = []
        for term in intro_terms:
            intro_conditions.append(f"introduce ILIKE ${param_idx}")
            params.append(f"%{term}%")
            param_idx += 1
        if intro_conditions:
            field_groups.append(f"({' OR '.join(intro_conditions)})")
    
    # cards filtering (JSONB) - already OR'd internally
    if search_filters.get('cards_contains'):
        cards_terms = search_filters['cards_contains']
        cards_conditions = []
        for term in cards_terms:
            cards_conditions.append(f"cards::text ILIKE ${param_idx}")
            params.append(f"%{term}%")
            param_idx += 1
        if cards_conditions:
            field_groups.append(f"({' OR '.join(cards_conditions)})")
    
    # Build final query - all field groups connected with OR
    if not field_groups:
        # No filters provided, return empty or use a default search
        logging.warning("No search filters provided, returning empty results")
        return []
    
    # Build score calculation: count matching keywords and skills for relevance scoring
    score_select_parts = []
    score_joins = []
    
    # Calculate match score based on overlapping keywords/skills
    if search_filters.get('keywords_any'):
        keywords_list = search_filters['keywords_any']
        score_select_parts.append(
            f"(SELECT COUNT(*) FROM jsonb_array_elements_text(keywords) AS kw WHERE kw.value = ANY(${param_idx}::text[]))"
        )
        params.append(keywords_list)
        param_idx += 1
    
    if search_filters.get('skills_any'):
        skills_list = search_filters['skills_any']
        if score_select_parts:
            score_select_parts.append(" + ")
        score_select_parts.append(
            f"(SELECT COUNT(*) FROM jsonb_array_elements_text(skills) AS sk WHERE sk.value = ANY(${param_idx}::text[]))"
        )
        params.append(skills_list)
        param_idx += 1
    
    match_score_expr = "".join(score_select_parts) if score_select_parts else "0"
    
    # Connect all field groups with OR to maximize candidate pool
    where_clause = " OR ".join(field_groups) if len(field_groups) > 1 else field_groups[0] if field_groups else "TRUE"
    
    query_parts = [
        "SELECT id, name, email, introduce, keywords, skills, cards, created_at,",
        f"{match_score_expr} as match_count",
        "FROM candidates",
        f"WHERE {where_clause}",
        f"ORDER BY match_count DESC, created_at DESC",
        f"LIMIT ${param_idx}"
    ]
    
    params.append(k)
    
    final_query = " ".join(query_parts)
    
    async with _pool.acquire() as connection:
        try:
            rows = await connection.fetch(final_query, *params)
        except Exception as e:
            logging.error(f"Structured search query failed: {final_query}")
            logging.error(f"Query parameters: {params}")
            logging.error(f"Search filters: {search_filters}")
            raise
    
    # Normalize match_count to score (0.0 to 1.0)
    results = []
    # Use total_terms for normalization, which was calculated at the beginning
    max_score = total_terms if total_terms > 0 else 1
    for row in rows:
        result = dict(row)
        result['id'] = str(result['id'])
        # Convert match_count to normalized score
        match_count = result.pop('match_count', 0)
        result['score'] = float(match_count) / max_score if max_score > 0 else 0.0
        results.append(result)
    
    return results

async def db_keyword_topk(persona: dict, k: int) -> list[dict]:
    """
    Performs a keyword-based search on the database using the new schema.
    Searches in name, introduce, and JSONB fields (keywords, skills, cards).
    
    Uses plainto_tsquery instead of to_tsquery to handle multi-word phrases better.
    """
    if _pool is None:
        raise ConnectionError("Database pool not initialized. Call connect_db() first.")

    # Extract keywords from various parts of the persona
    search_keywords = persona["persona"].get("skills_hard", [])
    search_terms = [skill['name'] for skill in search_keywords if isinstance(skill, dict)]
    search_terms.extend(persona["persona"].get("domains", []))
    search_terms.extend(persona["persona"].get("outcomes", []))
    search_terms = list(set(search_terms))  # Remove duplicates

    if not search_terms:
        # Fallback to query_text if no search terms found
        query_text = persona.get("persona", {}).get("query_text", "")
        if query_text:
            search_terms = [query_text]
        else:
            return []

    # Build search query string
    # plainto_tsquery is more lenient and handles multi-word phrases better
    # It automatically handles spaces and special characters
    query_str = ' '.join(search_terms)
    
    # Use plainto_tsquery which is more forgiving with natural language queries
    # It treats the input as plain text and converts it to a tsquery automatically
    query_parts = [
        "SELECT id, name, email, introduce, keywords, skills, cards, created_at, ",
        "ts_rank_cd(to_tsvector('english', ",
        "COALESCE(name, '') || ' ' || ",
        "COALESCE(introduce, '') || ' ' || ",
        "COALESCE(keywords::text, '') || ' ' || ",
        "COALESCE(skills::text, '') || ' ' || ",
        "COALESCE(cards::text, '')"
        "), query) as rank ",
        "FROM candidates, plainto_tsquery('english', $1) query ",
        "WHERE query @@ to_tsvector('english', ",
        "COALESCE(name, '') || ' ' || ",
        "COALESCE(introduce, '') || ' ' || ",
        "COALESCE(keywords::text, '') || ' ' || ",
        "COALESCE(skills::text, '') || ' ' || ",
        "COALESCE(cards::text, '')"
        ")"
    ]
    params = [query_str]
    param_idx = 2

    query_parts.append(f"ORDER BY rank DESC LIMIT ${param_idx}")
    params.append(k)

    final_query = " ".join(query_parts)

    async with _pool.acquire() as connection:
        try:
            rows = await connection.fetch(final_query, *params)
        except Exception as e:
            logging.error(f"Keyword search query failed: {final_query}")
            logging.error(f"Query parameters: {params}")
            logging.error(f"Search terms: {search_terms}")
            raise

    # Return results as list of dicts
    # Ensure ID is consistent (convert to string for consistency with vector search)
    results = []
    for row in rows:
        result = dict(row)
        # Normalize ID to string for consistency with vector search
        result['id'] = str(result['id'])
        results.append(result)
    return results