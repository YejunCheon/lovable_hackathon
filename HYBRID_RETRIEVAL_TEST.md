# Hybrid Retrieval 검증 가이드

이 문서는 Hybrid Retrieval 구현이 제대로 작동하는지 검증하는 방법을 안내합니다.

## 📋 사전 준비

1. **환경 변수 설정**
   - `.env` 파일에 다음 변수들이 설정되어 있어야 합니다:
     ```env
     GEMINI_API_KEY=your-key
     DB_HOST=localhost
     DB_PORT=5432
     DB_NAME=your_db
     DB_USER=your_user
     DB_PASSWORD=your_password
     QDRANT_URL=http://localhost:6333
     QDRANT_COLLECTION_NAME=candidates
     ```

2. **데이터 준비 확인**
   - ✅ PostgreSQL `candidates` 테이블에 데이터가 있어야 함
   - ✅ Qdrant에 벡터가 업로드되어 있어야 함
   - ✅ 각 후보의 `vector` 컬럼에 벡터 값이 있어야 함

## 🧪 검증 방법

### 방법 1: 전체 파이프라인 테스트 (권장)

전체 Hybrid Retrieval 파이프라인을 한 번에 테스트합니다.

```bash
# 가상환경 활성화
source venv/bin/activate

# 기본 쿼리로 테스트
python scripts/test_hybrid_retrieval.py

# 커스텀 쿼리로 테스트
python scripts/test_hybrid_retrieval.py --query "FPGA 연구 경험자 찾기"
```

**예상 출력:**
```
🚀 Hybrid Retrieval 검증 시작...

데이터베이스 연결 중...
Persona 생성 중... (쿼리: 인공지능 전문가, 머신러닝 연구자 찾기)
생성된 Persona:
  - Query Text: AI and machine learning researcher...
  - Domains: ['Machine Learning', 'AI']
  - Skills: [{'name': 'Python', 'level': 'advanced'}, ...]

Hybrid Retrieval 실행 중...

============================================================
검색 결과: 총 12개 후보 발견
============================================================

[1] 후보 ID: cand_123
    Score: 0.8542
    Name: 김교수
    Role: Professor
    Department: 컴퓨터공학과
    Keywords: AI, Machine Learning, Deep Learning
...
```

### 방법 2: 구성 요소별 테스트

각 구성 요소를 개별적으로 테스트하여 문제가 있는 부분을 정확히 파악할 수 있습니다.

```bash
# 가상환경 활성화
source venv/bin/activate

# 구성 요소별 테스트
python scripts/test_hybrid_components.py --query "인공지능 전문가 찾기"
```

**테스트되는 구성 요소:**
1. **Vector Search**: Qdrant를 통한 벡터 유사도 검색
2. **Keyword Search**: PostgreSQL을 통한 키워드 기반 검색
3. **Score Blending**: Vector와 Keyword 점수 융합
4. **MMR**: 다양성을 고려한 최종 후보 선택

## 📊 검증 체크리스트

### ✅ 정상 작동 시 확인 사항

- [ ] Persona가 제대로 생성되는가?
- [ ] Vector Search가 결과를 반환하는가?
- [ ] Keyword Search가 결과를 반환하는가?
- [ ] Score Blending이 제대로 작동하는가? (0~1 사이의 점수)
- [ ] MMR이 다양한 후보를 선택하는가?
- [ ] 최종 결과가 12개 이하로 반환되는가?

### ⚠️ 문제 발생 시 확인 사항

#### Vector Search가 작동하지 않을 때
1. **Qdrant 연결 확인**
   ```bash
   # Qdrant가 실행 중인지 확인
   curl http://localhost:6333/collections
   ```

2. **컬렉션 존재 확인**
   - Qdrant 대시보드에서 `candidates` 컬렉션이 있는지 확인
   - 또는 API로 확인: `curl http://localhost:6333/collections/candidates`

3. **벡터 업로드 확인**
   - Qdrant에 실제로 벡터가 업로드되어 있는지 확인
   - `candidates` 테이블의 `vector` 컬럼이 NULL이 아닌지 확인

#### Keyword Search가 작동하지 않을 때
1. **데이터베이스 연결 확인**
   - PostgreSQL이 실행 중인지 확인
   - `.env` 파일의 DB 설정이 올바른지 확인

2. **데이터 존재 확인**
   ```sql
   SELECT COUNT(*) FROM candidates;
   SELECT id, name, keywords, skills FROM candidates LIMIT 5;
   ```

3. **Full-text Search 인덱스 확인**
   ```sql
   -- 인덱스가 생성되어 있는지 확인
   SELECT indexname FROM pg_indexes WHERE tablename = 'candidates';
   ```

#### Score Blending이 작동하지 않을 때
- Vector Search와 Keyword Search 결과가 모두 비어있지 않은지 확인
- `blend_scores` 함수의 로직 확인

#### MMR이 작동하지 않을 때
- 벡터 조회가 제대로 되는지 확인
- `retrieve_vectors` 함수가 올바른 벡터를 반환하는지 확인

## 🔍 상세 디버깅

### 로그 레벨 변경

더 자세한 로그를 보려면 스크립트를 수정하세요:

```python
# scripts/test_hybrid_retrieval.py의 상단 부분
logging.basicConfig(
    level=logging.DEBUG,  # INFO -> DEBUG로 변경
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 개별 함수 테스트

특정 함수만 테스트하고 싶다면 Python REPL 사용:

```python
# 가상환경에서
python

>>> import asyncio
>>> from app.adapters import gemini, qdrant
>>> 
>>> async def test():
...     vec = await gemini.embed_query("AI researcher")
...     results = await qdrant.vector_topk(vec, k=5)
...     print(results)
... 
>>> asyncio.run(test())
```

## 📈 성능 확인

검색 성능을 측정하려면 스크립트에 타이밍을 추가하세요:

```python
import time

start = time.time()
results = await hybrid_retrieve(persona_dict)
elapsed = time.time() - start

logger.info(f"⏱️  검색 시간: {elapsed:.2f}초")
logger.info(f"⏱️  후보당 평균: {elapsed/len(results):.3f}초")
```

## 🎯 예상 결과

정상적으로 작동한다면:

- **Persona 생성**: 1-2초
- **Vector Search**: 0.1-0.5초
- **Keyword Search**: 0.1-0.3초
- **Score Blending**: < 0.01초
- **MMR**: 0.1-0.2초
- **전체 파이프라인**: 2-4초

## 💡 추가 팁

1. **다양한 쿼리로 테스트**
   - 짧은 쿼리: "AI"
   - 긴 쿼리: "FPGA 기반 딥러닝 가속 연구 경험이 있는 교수님 찾기"
   - 특정 도메인: "컴퓨터 비전 전문가"

2. **결과 품질 확인**
   - 반환된 후보들이 쿼리와 관련이 있는가?
   - 점수가 합리적인가? (너무 높거나 낮지 않은가?)
   - 다양한 후보들이 선택되었는가? (MMR 효과)

3. **에러 발생 시**
   - 에러 메시지를 자세히 읽어보세요
   - 로그를 통해 어느 단계에서 실패했는지 확인하세요
   - 각 구성 요소를 개별적으로 테스트해보세요

---

**문제가 발생하면** 로그와 에러 메시지를 함께 공유해주세요!

