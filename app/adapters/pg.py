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
    if _pool is None:
        try:
            # Supabase requires SSL connection
            # Create SSL context for Supabase (verify mode is CERT_NONE for Supabase's self-signed certs)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            logging.info(f"안녕하세요")
            
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
