
from app.adapters import gemini, pgvector, pg
from app.utils import scoring, mmr
import logging

logger = logging.getLogger(__name__)

async def hybrid_retrieve(persona: dict, use_vector_search: bool = True) -> list[dict]:
    """
    Orchestrates the hybrid retrieval process, including vector search, keyword search,
    score blending, and MMR for diversification.
    
    Uses pgvector for vector search (PostgreSQL native).
    
    Args:
        persona: Persona dictionary containing query information
        use_vector_search: If False, only use keyword search
    """
    logger.info("=" * 60)
    logger.info("2️⃣ Hybrid Retrieval 시작")
    logger.info("=" * 60)
    
    query_text = persona.get("persona", {}).get("query_text", "")
    if not query_text:
        logger.warning("⚠️  No query_text found in persona")
        return []

    vec_results = []
    kw_results = []
    
    # 1. Vector search using pgvector (PostgreSQL)
    if use_vector_search:
        logger.info("🔍 [Step 1/4] Vector Search (pgvector) 실행 중...")
        try:
            logger.info("   → Query embedding 생성 중...")
            query_vector = await gemini.embed_query(query_text)
            logger.info(f"   ✅ Embedding 생성 완료 (차원: {len(query_vector)})")
            
            logger.info("   → PostgreSQL에서 벡터 유사도 검색 중...")
            vec_results = await pgvector.vector_topk(query_vector, k=50)
            logger.info(f"   ✅ Vector search 완료: {len(vec_results)}개 결과")
            if vec_results:
                top_scores = [f"{r.get('score', 0):.4f}" for r in vec_results[:3]]
                logger.info(f"   📊 상위 3개 점수: {top_scores}")
        except Exception as e:
            logger.warning(f"   ⚠️  Vector search 실패, Keyword search만 사용: {e}", exc_info=True)
            vec_results = []
    else:
        logger.info("🔍 [Step 1/4] Vector Search 비활성화 (Keyword search만 사용)")

    # 2. Fetch from keyword search
    logger.info("🔍 [Step 2/4] Keyword Search (PostgreSQL full-text) 실행 중...")
    try:
        logger.info("   → PostgreSQL full-text search 쿼리 실행 중...")
        kw_results = await pg.db_keyword_topk(persona, k=50)
        logger.info(f"   ✅ Keyword search 완료: {len(kw_results)}개 결과")
        if kw_results:
            logger.info(f"   📊 상위 3개 후보 ID: {[r.get('id') for r in kw_results[:3]]}")
    except Exception as e:
        logger.error(f"   ❌ Keyword search 실패: {e}", exc_info=True)
        # If keyword search fails, return vector results if available
        if vec_results:
            logger.info("   → Vector search 결과만 반환")
            return vec_results[:12]  # Return top 12
        return []

    # 3. If we have results from both, blend them
    logger.info("🔀 [Step 3/4] Score Blending 실행 중...")
    if vec_results and kw_results:
        logger.info(f"   → Vector: {len(vec_results)}개, Keyword: {len(kw_results)}개")
        logger.info("   → Blending 가중치: Vector 60%, Keyword 40% (alpha=0.6)")
        # Blend the scores (alpha=0.6 means 60% weight for vector, 40% for keyword)
        blended_results = scoring.blend_scores(vec_results, kw_results, alpha=0.6)
        logger.info(f"   ✅ Blended 완료: {len(blended_results)}개 결과")
        if blended_results:
            top_scores = [f"{r.get('score', 0):.4f}" for r in blended_results[:3]]
            logger.info(f"   📊 Blended 상위 3개 점수: {top_scores}")
    elif kw_results:
        # Only keyword results available
        blended_results = kw_results
        logger.info(f"   → Vector 결과 없음. Keyword만 사용: {len(blended_results)}개")
    elif vec_results:
        # Only vector results available
        blended_results = vec_results
        logger.info(f"   → Keyword 결과 없음. Vector만 사용: {len(blended_results)}개")
    else:
        logger.warning("   ⚠️  Vector와 Keyword 검색 모두 결과 없음")
        return []

    # 4. Apply MMR for diversity (if we have enough results and vectors available)
    logger.info("🎯 [Step 4/4] MMR (다양성 적용) 실행 중...")
    # Normalize IDs to strings for consistency (pgvector.retrieve_vectors expects string keys in result)
    top_ids_for_mmr = [str(doc['id']) for doc in blended_results[:20]]
    if not top_ids_for_mmr:
        logger.info("   → MMR 적용할 후보 없음")
        logger.info("=" * 60)
        return []

    # Use MMR for diversity if we have vectors available
    if len(blended_results) > 1:
        try:
            logger.info(f"   → 상위 {len(top_ids_for_mmr)}개 후보의 벡터 조회 중...")
            # retrieve_vectors accepts list of IDs (can be int or str), returns dict with string keys
            doc_vectors = await pgvector.retrieve_vectors(top_ids_for_mmr)
            if doc_vectors and len(doc_vectors) > 0:
                logger.info(f"   ✅ {len(doc_vectors)}개 벡터 조회 완료")
                logger.info("   → MMR 알고리즘 적용 중... (lambda=0.5, k=12)")
                # Apply MMR if we have vectors
                diverse_results = mmr.mmr(blended_results[:20], doc_vectors, lambda_val=0.5, k=12)
                logger.info(f"   ✅ MMR 완료: {len(diverse_results)}개 다양한 결과")
                logger.info("=" * 60)
                return diverse_results
            else:
                logger.info("   → 벡터 조회 실패, MMR 스킵")
        except Exception as e:
            logger.warning(f"   ⚠️  MMR 실패, 상위 결과 반환: {e}")
    else:
        logger.info("   → 결과가 1개 이하, MMR 스킵")
    
    # If MMR is not available or failed, return top 12 results
    final_count = min(12, len(blended_results))
    logger.info(f"   ✅ 최종 {final_count}개 결과 반환 (MMR 없이)")
    logger.info("=" * 60)
    return blended_results[:12]
