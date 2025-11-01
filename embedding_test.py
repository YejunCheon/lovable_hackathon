import json
import os
import time

from dotenv import load_dotenv
from google import genai

from app.adapters.pg import connect_db, execute_query

load_dotenv()

# Gemini API 키 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")

client = genai.Client(api_key=GEMINI_API_KEY)
     
MODEL_ID = "gemini-embedding-001"

async def main():
    pool = await connect_db()
    records = await execute_query("SELECT id, introduce, keywords, skills FROM candidates")

    all_text_dump = []

    for record in records:
        introduce = record['introduce']
        keywords = json.loads(record['keywords'])
        skills = json.loads(record['skills'])

        all_text_dump.extend(keywords)
        all_text_dump.extend(skills)
        all_text_dump.append(introduce)

    already_exist = [record['text'] for record in await execute_query("SELECT text FROM text_embeddings")]
    all_text_dump = list(set(all_text_dump) - set(already_exist))
    
    print(all_text_dump, len(all_text_dump))

    BATCH_SIZE = 10

    for i in range(0, len(all_text_dump), BATCH_SIZE):
        print(f"Processing batch {i} to {i+BATCH_SIZE}")
        batch = all_text_dump[i:i+BATCH_SIZE]
        result = client.models.embed_content(
            model=MODEL_ID,
            contents=batch)

        tuples = []

        for content, embedding in zip(batch, result.embeddings):
            tuples.append((content, str(embedding.values)))

        async with pool.acquire() as connection:
            await connection.executemany("INSERT INTO text_embeddings (text, vector) VALUES ($1, $2)", tuples)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
