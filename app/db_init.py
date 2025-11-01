import asyncio
import logging
from app.adapters.pg import connect_db, close_db, execute_query
from app.core.config import settings
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

async def initialize_db():
    logging.info("Starting database initialization...")
    try:
        await connect_db()

        ddl_statements = """
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        CREATE EXTENSION IF NOT EXISTS "vector";

        CREATE TABLE IF NOT EXISTS orgs (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          name TEXT NOT NULL,
          created_at TIMESTAMPTZ DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS users (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
          email TEXT UNIQUE NOT NULL,
          role TEXT DEFAULT 'member',
          created_at TIMESTAMPTZ DEFAULT now()
        );

        CREATE TABLE IF NOT EXISTS candidates (
          id SERIAL PRIMARY KEY,
          name TEXT NOT NULL,
          email TEXT NOT NULL UNIQUE,
          introduce TEXT,
          keywords JSONB,
          skills JSONB,
          cards JSONB,
          vector VECTOR(1536),
          created_at TIMESTAMP DEFAULT now()
        );

        CREATE INDEX IF NOT EXISTS idx_candidates_email ON candidates (email);
        CREATE INDEX IF NOT EXISTS idx_candidates_keywords_gin ON candidates USING GIN (keywords);
        CREATE INDEX IF NOT EXISTS idx_candidates_skills_gin ON candidates USING GIN (skills);
        CREATE INDEX IF NOT EXISTS idx_candidates_cards_gin ON candidates USING GIN (cards);
        CREATE INDEX IF NOT EXISTS idx_candidates_vector ON candidates USING ivfflat (vector vector_cosine_ops);

        CREATE TABLE IF NOT EXISTS search_audit (
          id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
          org_id UUID REFERENCES orgs(id),
          user_id UUID REFERENCES users(id),
          persona_json JSONB NOT NULL,
          topk_ids TEXT[] NOT NULL,
          latency_ms INT,
          created_at TIMESTAMPTZ DEFAULT now()
        );
        """
        # Split by semicolon and filter out empty strings
        statements = [s.strip() for s in ddl_statements.split(';') if s.strip()]

        for statement in statements:
            logging.info(f"Executing DDL: {statement[:70]}...") # Log first 70 chars
            await execute_query(statement)
        
        logging.info("Database initialization completed successfully.")

    except Exception as e:
        logging.error(f"Database initialization failed: {e}")
        raise
    finally:
        await close_db()

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(initialize_db())
