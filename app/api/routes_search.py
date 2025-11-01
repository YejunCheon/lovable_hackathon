from fastapi import APIRouter, HTTPException
from app.schemas.search import SearchRequest, SearchResponse, CandidateSearchResult
from app.services.persona import build_persona
from app.services.retrieve import hybrid_retrieve
from app.services.judge import judge_parallel
from app.adapters.pg import _pool
import logging
import time
import json
from typing import List, Dict, Any

router = APIRouter()


async def load_candidate_details(candidate_ids: List[int]) -> Dict[int, Dict[str, Any]]:
    """
    Loads full candidate details from database by IDs.
    Returns a dictionary mapping candidate ID to candidate data.
    """
    from app.adapters.pg import connect_db, _pool
    
    # Import pool dynamically to ensure it's current
    if _pool is None:
        logging.warning("Database pool not initialized. Attempting to connect...")
        try:
            await connect_db()
            # Re-import after connection
            from app.adapters.pg import _pool as _pool_after
            if _pool_after is None:
                raise ConnectionError("Failed to initialize database pool after retry.")
            logging.info("Database pool initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to connect to database: {e}")
            raise ConnectionError(f"Database connection failed: {e}")
    
    # Use the current pool
    from app.adapters.pg import _pool as pool
    
    if not candidate_ids:
        return {}
    
    try:
        query = """
            SELECT 
                id, name, email, introduce, keywords, skills, cards, created_at
            FROM candidates
            WHERE id = ANY($1::int[])
        """
        
        async with pool.acquire() as connection:
            rows = await connection.fetch(query, candidate_ids)
        
        result = {}
        for row in rows:
            candidate_id = row['id']
            
            # Parse JSONB fields - asyncpg returns JSONB as Python objects, but sometimes as strings
            # Helper function to safely parse JSONB fields
            def parse_jsonb_field(value):
                if value is None:
                    return []
                if isinstance(value, str):
                    try:
                        parsed = json.loads(value)
                        return parsed if isinstance(parsed, list) else []
                    except (json.JSONDecodeError, TypeError):
                        return []
                if isinstance(value, list):
                    return value
                return []
            
            keywords = parse_jsonb_field(row.get('keywords'))
            skills = parse_jsonb_field(row.get('skills'))
            cards = parse_jsonb_field(row.get('cards'))
            
            result[candidate_id] = {
                "id": candidate_id,
                "name": row.get('name', ''),
                "description": row.get('introduce'),
                "keywords": keywords,
                "skills": skills,
                "cards": cards,
                "email": row.get('email'),
                "created_at": row.get('created_at').isoformat() if row.get('created_at') else None,
            }
        
        return result
    except Exception as e:
        logging.error(f"Failed to load candidate details: {e}", exc_info=True)
        return {}


@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest) -> SearchResponse:
    """
    Search for candidates using Hybrid Retrieval (Vector + Keyword search).
    Returns top 4 candidates with full details matching PRD specification.
    """
    start_time = time.time()
    logging.info("\n" + "=" * 60)
    logging.info("🚀 Search API 요청 시작")
    logging.info("=" * 60)
    logging.info(f"📥 요청: {req.query_text}")
    
    try:
        # 1. Build persona from query
        logging.info("\n[Phase 1] Persona 생성 단계")
        persona_response = await build_persona(req)
        persona_dict = persona_response.model_dump()
        query_summary = persona_dict.get("persona", {}).get("query_text", req.query_text)
        
        # 2. Perform Hybrid Retrieval
        logging.info("\n[Phase 2] Hybrid Retrieval 단계")
        retrieval_results = await hybrid_retrieve(persona_dict, use_vector_search=True)
        
        if not retrieval_results:
            logging.warning("⚠️  검색 결과 없음")
            latency_ms = int((time.time() - start_time) * 1000)
            logging.info(f"⏱️  총 소요 시간: {latency_ms}ms")
            logging.info("=" * 60 + "\n")
            return SearchResponse(
                query_summary=query_summary,
                candidates_top4=[],
                latency_ms=latency_ms
            )
        
        # 3. AI as Judge
        logging.info("\n[Phase 3] AI as Judge 단계")
        candidates_for_judging = retrieval_results[:12] # Top 12 for judging
        candidate_ids_for_judging = [int(c['id']) for c in candidates_for_judging]
        
        logging.info(f"   → 상위 {len(candidate_ids_for_judging)}명 후보 상세 정보 로드")
        detailed_candidates_for_judging = await load_candidate_details(candidate_ids_for_judging)

        if not detailed_candidates_for_judging:
            raise Exception("Could not load details for judging candidates.")

        # Convert dict to list for judge_parallel
        candidates_list = [detailed_candidates_for_judging[cid] for cid in candidate_ids_for_judging if cid in detailed_candidates_for_judging]

        logging.info(f"   → {len(candidates_list)}명 후보에 대한 병렬 평가 시작")
        judged_results = await judge_parallel(candidates_list, persona_dict)
        
        # Sort by fit_score from judge
        judged_results.sort(key=lambda x: x.get('fit_score', 0), reverse=True)
        
        final_candidates = judged_results[:4]
        logging.info(f"   → 최종 후보 4명 선택 완료")

        # 4. Build response
        logging.info("\n[Phase 4] 응답 구성")
        candidates_top4 = []
        for judged_cand in final_candidates:
            cand_id = int(judged_cand['candidate_id'])
            details = detailed_candidates_for_judging.get(cand_id, {})
            
            candidate_result = CandidateSearchResult(
                id=cand_id,
                name=details.get('name', ''),
                description=details.get('description'),
                keywords=details.get('keywords', []),
                skills=details.get('skills', []),
                cards=details.get('cards', []),
                fit_score=judged_cand.get('fit_score', 0.0),
                reason_ko=judged_cand.get('reason_ko'),
                email=details.get('email'),
                created_at=details.get('created_at')
            )
            candidates_top4.append(candidate_result)
            logging.info(f"   ✅ {details.get('name', 'Unknown')} (ID: {cand_id}, Score: {judged_cand.get('fit_score', 0):.2f})")
        
        latency_ms = int((time.time() - start_time) * 1000)
        logging.info(f"\n⏱️  총 소요 시간: {latency_ms}ms")
        logging.info(f"✅ 검색 완료: {len(candidates_top4)}개 후보 반환")
        logging.info("=" * 60 + "\n")
        
        return SearchResponse(
            query_summary=query_summary,
            candidates_top4=candidates_top4,
            latency_ms=latency_ms
        )
        
    except Exception as e:
        logging.error(f"Error during search: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )