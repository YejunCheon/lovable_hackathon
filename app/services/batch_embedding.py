
from typing import List

from google.genai import Client
from pydantic import BaseModel

from main import GEMINI_API_KEY

client = Client(api_key=GEMINI_API_KEY)
MODEL_ID = "gemini-embedding-001"

def batch_embedding(texts: List[str]) -> List[str]:
    result = client.models.embed_content(
        model=MODEL_ID,
        contents=texts
    )

    return [embedding.values for embedding in result.embeddings]
