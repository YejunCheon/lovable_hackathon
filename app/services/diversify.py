
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
            "system_instruction": """
Diversify following search query into specific word-level queries, each query should be 2~3 words long. Create 10 various and dynamic queries.

Example1: 클라우드 개발 해본 사람 없나
Output: ['AWS 개발 경험', '클라우드 엔지니어', '백엔드 개발', '클라우드 아키텍트', 'DevOps', '인프라 엔지니어', 'SRE 운영', '마이크로서비스 아키텍처', '서버리스 개발']

Example2: 커피 좋아하는 사람
Output: ['커피 취미', '스페셜티 로스팅', '카페 운영', '커피 소믈리에', '바리스타 경력', '에스프레소 머신', '핸드드립', '홈카페', '로스팅 클래스']
"""
        }
    )

    print("Diversified", response.parsed.search_queries)

    return response.parsed.search_queries
