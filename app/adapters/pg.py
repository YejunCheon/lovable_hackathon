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
        # Use connection.fetch for SELECT queries that return rows
        # Use connection.execute for INSERT, UPDATE, DELETE, DDL that don't return rows
        if query.strip().lower().startswith("select"):
            return await connection.fetch(query, *args)
        else:
            return await connection.execute(query, *args)

async def fetch_one(query: str, *args):
    """
    Executes a SQL query and returns a single row.
    """
    if _pool is None:
        raise ConnectionError("Database pool not initialized. Call connect_db() first.")
    
    async with _pool.acquire() as connection:
        return await connection.fetchrow(query, *args)

async def fetch_val(query: str, *args):
    """
    Executes a SQL query and returns a single value.
    """
    if _pool is None:
        raise ConnectionError("Database pool not initialized. Call connect_db() first.")
    
    async with _pool.acquire() as connection:
        return await connection.fetchval(query, *args)

async def db_keyword_topk(persona: dict, k: int) -> list[dict]:
    """
    Performs a keyword-based search on the database using the new schema.
    Searches in name, introduce, and JSONB fields (keywords, skills, cards).
    """
    if _pool is None:
        raise ConnectionError("Database pool not initialized. Call connect_db() first.")

    # Extract keywords from various parts of the persona
    search_keywords = persona["persona"].get("skills_hard", [])
    search_terms = [skill['name'] for skill in search_keywords if isinstance(skill, dict)]
    search_terms.extend(persona["persona"].get("domains", []))
    search_terms.extend(persona["persona"].get("outcomes", []))
    search_terms = list(set(search_terms)) # Remove duplicates

    if not search_terms:
        return []

    # Build search query for JSONB fields and text fields
    # JSONB fields need to be converted to text for full-text search
    query_str = ' | '.join(search_terms)
    
    query_parts = [
        "SELECT id, name, email, introduce, keywords, skills, cards, created_at, "
        "ts_rank_cd(to_tsvector('english', "
        "COALESCE(name, '') || ' ' || "
        "COALESCE(introduce, '') || ' ' || "
        "COALESCE(keywords::text, '') || ' ' || "
        "COALESCE(skills::text, '') || ' ' || "
        "COALESCE(cards::text, '')"
        "), query) as rank "
        "FROM candidates, to_tsquery('english', $1) query "
        "WHERE query @@ to_tsvector('english', "
        "COALESCE(name, '') || ' ' || "
        "COALESCE(introduce, '') || ' ' || "
        "COALESCE(keywords::text, '') || ' ' || "
        "COALESCE(skills::text, '') || ' ' || "
        "COALESCE(cards::text, '')"
        ")"
    ]
    params = [query_str]
    param_idx = 2

    query_parts.append(f"ORDER BY rank DESC LIMIT ${param_idx}")
    params.append(k)

    final_query = " ".join(query_parts)

    async with _pool.acquire() as connection:
        rows = await connection.fetch(final_query, *params)

    return [dict(row) for row in rows]
