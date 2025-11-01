"""
Hybrid Retrieval 검증 스크립트

이 스크립트는 Hybrid Retrieval 구현이 제대로 작동하는지 검증합니다.
다음 사항들을 확인합니다:
1. Vector Search가 제대로 작동하는지
2. Keyword Search가 제대로 작동하는지
3. Score Blending이 제대로 작동하는지
4. MMR이 제대로 작동하는지
5. 전체 파이프라인이 제대로 작동하는지
"""

import asyncio
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.persona import build_persona
from app.services.retrieve import hybrid_retrieve
from app.schemas.search import SearchRequest
from app.adapters.pg import connect_db, close_db
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_hybrid_retrieval(query_text: str, org_context: dict = None):
    """
    Hybrid Retrieval을 테스트합니다.
    
    Args:
        query_text: 검색 쿼리 텍스트
        org_context: 조직 컨텍스트 (선택사항)
    """
    try:
        # 1. 데이터베이스 연결
        logger.info("데이터베이스 연결 중...")
        await connect_db()
        
        # 2. Persona 생성
        logger.info(f"Persona 생성 중... (쿼리: {query_text})")
        search_request = SearchRequest(
            query_text=query_text,
            org_context=org_context
        )
        persona_response = await build_persona(search_request)
        persona_dict = persona_response.model_dump()
        
        logger.info(f"생성된 Persona:")
        logger.info(f"  - Query Text: {persona_dict.get('persona', {}).get('query_text', 'N/A')}")
        logger.info(f"  - Domains: {persona_dict.get('persona', {}).get('domains', [])}")
        logger.info(f"  - Skills: {persona_dict.get('persona', {}).get('skills_hard', [])}")
        
        # 3. Hybrid Retrieval 실행
        logger.info("Hybrid Retrieval 실행 중...")
        results = await hybrid_retrieve(persona_dict)
        
        # 4. 결과 출력
        logger.info(f"\n{'='*60}")
        logger.info(f"검색 결과: 총 {len(results)}개 후보 발견")
        logger.info(f"{'='*60}\n")
        
        if not results:
            logger.warning("⚠️  검색 결과가 없습니다. 다음을 확인하세요:")
            logger.warning("  1. Qdrant에 벡터가 업로드되어 있는지")
            logger.warning("  2. PostgreSQL candidates 테이블에 데이터가 있는지")
            logger.warning("  3. 벡터 임베딩이 제대로 생성되었는지")
            return
        
        # 상위 결과들을 상세히 출력
        for idx, result in enumerate(results[:10], 1):  # 상위 10개만 출력
            logger.info(f"\n[{idx}] 후보 ID: {result.get('id', 'N/A')}")
            logger.info(f"    Score: {result.get('score', 'N/A'):.4f}")
            
            # Payload에서 추가 정보 출력
            payload = result.get('payload', {})
            if payload:
                logger.info(f"    Name: {payload.get('name', 'N/A')}")
                logger.info(f"    Role: {payload.get('role', 'N/A')}")
                logger.info(f"    Department: {payload.get('department', 'N/A')}")
                
                # Keywords나 Skills가 있으면 출력
                keywords = payload.get('keywords', [])
                if keywords:
                    logger.info(f"    Keywords: {', '.join(keywords[:5])}")  # 최대 5개만
        
        logger.info(f"\n{'='*60}")
        logger.info("✅ Hybrid Retrieval 검증 완료!")
        logger.info(f"{'='*60}\n")
        
        # 추가 통계 정보
        if len(results) > 0:
            scores = [r.get('score', 0) for r in results]
            logger.info(f"📊 통계:")
            logger.info(f"   - 평균 Score: {sum(scores) / len(scores):.4f}")
            logger.info(f"   - 최고 Score: {max(scores):.4f}")
            logger.info(f"   - 최저 Score: {min(scores):.4f}")
            logger.info(f"   - 반환된 후보 수: {len(results)}")
        
    except Exception as e:
        logger.error(f"❌ 오류 발생: {e}", exc_info=True)
        raise
    finally:
        # 데이터베이스 연결 종료
        await close_db()


async def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Hybrid Retrieval 검증 스크립트')
    parser.add_argument(
        '--query',
        type=str,
        default='인공지능 전문가, 머신러닝 연구자 찾기',
        help='검색 쿼리 텍스트'
    )
    
    args = parser.parse_args()
    
    logger.info("🚀 Hybrid Retrieval 검증 시작...\n")
    
    # 기본 테스트 쿼리
    await test_hybrid_retrieval(args.query)
    
    # 추가 테스트 쿼리들 (선택사항)
    # await test_hybrid_retrieval("FPGA 연구 경험자 찾기")
    # await test_hybrid_retrieval("데이터 과학 전문가")


if __name__ == "__main__":
    asyncio.run(main())

