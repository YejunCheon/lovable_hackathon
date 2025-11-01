from pydantic import BaseModel
from typing import Optional, Dict, Any

class SearchRequest(BaseModel):
    query_text: str
    org_context: Optional[Dict[str, Any]] = None
