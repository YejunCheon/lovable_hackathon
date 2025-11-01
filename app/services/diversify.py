
from typing import List

from google.genai import Client
from pydantic import BaseModel

from main import GEMINI_API_KEY

client = Client(api_key=GEMINI_API_KEY)

class Response(BaseModel):
    search_queries: List[str]

def diversify_search_query(search_query: str) -> List[str]:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=search_query,
        config = {
            "thinkingConfig": {"thinking_budget": 0},
            "response_mime_type": "application/json",
            "response_schema": Response,
            "system_instruction": "Diversify following search query into specific word-level queries, each query should be 2~3 words long. Create 12 queries."
        }
    )

    return response.parsed.search_queries
