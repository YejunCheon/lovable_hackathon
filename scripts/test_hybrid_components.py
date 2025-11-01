"""
Hybrid Retrieval 구성 요소별 검증 스크립트

각 구성 요소를 개별적으로 테스트합니다:
1. Vector Search만 테스트
2. Keyword Search만 테스트
3. Score Blending 테스트
4. MMR 테스트
"""

import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.persona import build_persona
from app.schemas.search import SearchRequest
from app.adapters import gemini, qdrant, pg
from app.utils import scoring, mmr
from app.adapters.pg import connect_db, close_db
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_vector_search(query_text: str):
    """Vector Search만 테스트"""
    logger.info("\n" + "="*60)
    logger.info("1️⃣ Vector Search 테스트")
    logger.info("="*60)
    
    try:
        # Query embedding 생성
        query_vector = await gemini.embed_query(query_text)
        logger.info(f"✅ Query embedding 생성 완료 (벡터 차원: {len(query_vector)})")
        
        # Vector search 실행
        results = await qdrant.vector_topk(query_vector, k=10)
        logger.info(f"✅ Vector search 완료: {len(results)}개 결과")
        
        for idx, result in enumerate(results[:5], 1):
            logger.info(f"   [{idx}] ID: {result.get('id')}, Score: {result.get('score', 0):.4f}")
        
        return results
    except Exception as e:
        logger.error(f"❌ Vector Search 실패: {e}", exc_info=True)
        return []


async def test_keyword_search(persona_dict: dict):
    """Keyword Search만 테스트"""
    logger.info("\n" + "="*60)
    logger.info("2️⃣ Keyword Search 테스트")
    logger.info("="*60)
    
    try:
        results = await pg.db_keyword_topk(persona_dict, k=10)
        logger.info(f"✅ Keyword search 완료: {len(results)}개 결과")
        
        for idx, result in enumerate(results[:5], 1):
            logger.info(f"   [{idx}] ID: {result.get('id')}, Rank: {result.get('rank', 0):.4f}")
        
        return results
    except Exception as e:
        logger.error(f"❌ Keyword Search 실패: {e}", exc_info=True)
        return []


async def test_score_blending(vec_results: list, kw_results: list):
    """Score Blending 테스트"""
    logger.info("\n" + "="*60)
    logger.info("3️⃣ Score Blending 테스트")
    logger.info("="*60)
    
    try:
        blended = scoring.blend_scores(vec_results, kw_results, alpha=0.6)
        logger.info(f"✅ Score blending 완료: {len(blended)}개 결과")
        
        logger.info("   상위 5개 결과:")
        for idx, result in enumerate(blended[:5], 1):
            logger.info(f"   [{idx}] ID: {result.get('id')}, Blended Score: {result.get('score', 0):.4f}")
        
        return blended
    except Exception as e:
        logger.error(f"❌ Score Blending 실패: {e}", exc_info=True)
        return []


async def test_mmr(blended_results: list):
    """MMR 테스트"""
    logger.info("\n" + "="*60)
    logger.info("4️⃣ MMR (다양성) 테스트")
    logger.info("="*60)
    
    try:
        # 상위 20개에 대해 MMR 적용
        top_20 = blended_results[:20]
        top_ids = [doc['id'] for doc in top_20]
        
        if not top_ids:
            logger.warning("⚠️  MMR 테스트할 후보가 없습니다.")
            return []
        
        # 벡터 조회
        doc_vectors = await qdrant.retrieve_vectors(top_ids)
        logger.info(f"✅ 벡터 조회 완료: {len(doc_vectors)}개")
        
        # MMR 적용
        diverse_results = mmr.mmr(top_20, doc_vectors, lambda_val=0.5, k=12)
        logger.info(f"✅ MMR 완료: {len(diverse_results)}개 결과")
        
        logger.info("   MMR로 선택된 후보들:")
        for idx, result in enumerate(diverse_results[:5], 1):
            logger.info(f"   [{idx}] ID: {result.get('id')}, Score: {result.get('score', 0):.4f}")
        
        return diverse_results
    except Exception as e:
        logger.error(f"❌ MMR 실패: {e}", exc_info=True)
        return []


async def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Hybrid Retrieval 구성 요소별 검증')
    parser.add_argument(
        '--query',
        type=str,
        default='인공지능 전문가, 머신러닝 연구자 찾기',
        help='검색 쿼리 텍스트'
    )
    
    args = parser.parse_args()
    
    logger.info("🚀 Hybrid Retrieval 구성 요소별 검증 시작...\n")
    
    try:
        # 데이터베이스 연결
        await connect_db()
        
        # Persona 생성
        logger.info("Persona 생성 중...")
        search_request = SearchRequest(query_text=args.query)
        persona_response = await build_persona(search_request)
        persona_dict = persona_response.model_dump()
        
        query_text = persona_dict.get('persona', {}).get('query_text', args.query)
        
        # 각 구성 요소 테스트
        vec_results = await test_vector_search(query_text)
        kw_results = await test_keyword_search(persona_dict)
        
        if vec_results and kw_results:
            blended = await test_score_blending(vec_results, kw_results)
            
            if blended:
                diverse = await test_mmr(blended)
                
                logger.info("\n" + "="*60)
                logger.info("✅ 모든 구성 요소 검증 완료!")
                logger.info("="*60 + "\n")
        
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}", exc_info=True)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())

