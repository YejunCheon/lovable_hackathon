

🧭 AI 인재 검색 플랫폼 – 백엔드 테크 스펙 & 구현 가이드 (문서형, 범용 확장 스키마 반영)

0. 목적

자연어 질의로 조직에 적합한 인재를 찾고, LLM + RDB + Vector Search를 결합해 정확·빠른 추천을 제공한다.
실행 환경은 Gemini API(Google) 기반으로 inference를 수행하며,
인재의 직군(교수, 연구원, 엔지니어, 마케터, 운동선수 등)에 따라 다른 구조의 정보를 저장할 수 있도록
**정형 공통 컬럼 + 비정형 JSON 확장 구조(JSONB)**를 채택한다.

⸻

1. 시스템 아키텍처

1.1 논리 구성

[Client(Web/App)]
    │  REST/SSE/WebSocket
    ▼
[FastAPI Gateway]
    ├─ AuthN/AuthZ (OIDC/OAuth2)
    ├─ Rate Limit / WAF
    ├─ Request Orchestrator (async)
    │     ├─ Persona Builder (Gemini)
    │     ├─ Retriever:
    │     │     ├─ Vector Search (Qdrant/pgvector)
    │     │     └─ DB Filter (PostgreSQL)
    │     └─ AI Judge (Gemini Flash, parallel)
    ├─ ProfileCard Assembler
    └─ Telemetry (OTel)
    ▼
[Data Layer]
    ├─ PostgreSQL (profiles, org, audit)
    ├─ Vector DB (Qdrant or pgvector)
    └─ Object Storage (GCS/S3: raw/md)

1.2 배포 토폴로지
	•	FastAPI: Uvicorn(ASGI) 기반 컨테이너 이미지
	•	DB: Cloud SQL for PostgreSQL (또는 Supabase)
	•	Vector: Qdrant Cloud(권장) 또는 pgvector (≤100k 데이터)
	•	Storage: GCS(마크다운, 아바타, 원문 저장)
⸻

2. 데이터 모델

2.1 범용 Persona 스키마 (LLM 출력)

{
  "persona": {
    "titles": ["Professor", "Research Engineer", "ML Engineer"],
    "domains": ["Computer Vision", "FPGA", "HRI"],
    "skills_hard": [{"name": "CUDA", "level": "advanced"}, {"name": "PyTorch", "level": "advanced"}],
    "skills_soft": ["mentoring", "cross-team collaboration"],
    "seniority": ["junior", "mid", "senior"],
    "outcomes": ["first-author top-tier papers", "shipped inference infra"],
    "constraints_hard": {
      "location_any_of": ["Seoul", "Incheon"],
      "must_have": ["PhD or equivalent publications"]
    },
    "preferences_soft": {
      "nice_to_have": ["industry collaboration", "grant management"],
      "weights": {
        "domains": 0.25, "skills_hard": 0.35, "skills_soft": 0.10,
        "outcomes": 0.20, "preferences": 0.10
      }
    },
    "org_context": {
      "mission": "AI 가속기 공동 연구",
      "stack": ["Python", "C++", "CUDA", "Verilog"],
      "collab_style": ["weekly sync", "doc-first"]
    },
    "query_text": "FPGA 기반 AI 가속, 산학협력 경험, PyTorch/CUDA 실무"
  }
}


⸻

2.2 RDB 스키마 (PostgreSQL + JSON 확장형)

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

CREATE TABLE orgs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id UUID NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
  email TEXT UNIQUE NOT NULL,
  role TEXT DEFAULT 'member',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 핵심 테이블: 후보자(인재)
CREATE TABLE candidates (
  id TEXT PRIMARY KEY,
  org_scope UUID REFERENCES orgs(id),
  name TEXT NOT NULL,
  role TEXT,                                -- 예: 'Professor', 'Marketer', 'Athlete'
  titles TEXT[],
  department TEXT,
  location TEXT,
  keywords TEXT[],                          -- 공통 키워드
  skills TEXT[],                            -- 핵심 스킬
  summary TEXT,                             -- 요약 설명
  profile_md TEXT,                          -- 원문 Markdown
  avatar_url TEXT,
  vector VECTOR(1536),                      -- 요약/소개 임베딩 벡터
  custom_data JSONB DEFAULT '{}'::jsonb,    -- 직군별 커스터마이징 데이터
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 검색 최적화용 인덱스
CREATE INDEX idx_candidates_keywords ON candidates USING GIN (keywords);
CREATE INDEX idx_candidates_location ON candidates (location);
CREATE INDEX idx_candidates_role ON candidates (role);
CREATE INDEX idx_candidates_vector ON candidates USING ivfflat (vector vector_cosine_ops);
CREATE INDEX idx_candidates_custom_data_gin ON candidates USING GIN (custom_data jsonb_path_ops);

-- 검색/감사 로그
CREATE TABLE search_audit (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  org_id UUID REFERENCES orgs(id),
  user_id UUID REFERENCES users(id),
  persona_json JSONB NOT NULL,
  topk_ids TEXT[] NOT NULL,
  latency_ms INT,
  created_at TIMESTAMPTZ DEFAULT now()
);


⸻

2.3 custom_data 예시

👨‍🏫 교수 (Professor)

{
  "publications": [
    {"title": "FPGA Acceleration for CNNs", "year": 2023, "venue": "IEEE", "link": "https://..."},
    {"title": "Efficient Logic Design", "year": 2021}
  ],
  "conferences": [
    {"name": "DAC 2024", "role": "Keynote Speaker"}
  ],
  "grants": [
    {"title": "AI Accelerator Research", "amount": 30000000, "sponsor": "NRF"}
  ]
}

💼 마케터 (Marketer)

{
  "campaigns": [
    {"name": "Samsung Galaxy S24 Launch", "role": "Digital Strategist", "reach": "15M", "year": 2024}
  ],
  "platform_experience": ["Google Ads", "Meta Ads", "TikTok For Business"],
  "case_studies": [
    {"title": "UGC Campaign with 45% CTR uplift"}
  ]
}

🏃 운동선수 (Athlete)

{
  "sports": "Swimming",
  "records": [
    {"event": "100m Freestyle", "time": "00:51.3", "competition": "National Univ Championship", "year": 2024}
  ],
  "awards": [{"title": "MVP", "year": 2024, "competition": "College League"}]
}


⸻

2.4 규모 선택 가이드
	•	≤ 100k 후보: PostgreSQL + pgvector
	•	100k 후보 / 고QPS: Qdrant/Weaviate

⸻

3. 검색·랭킹 파이프라인

3.1 단계 요약

1️⃣ Persona Builder (Gemini Flash)
→ 자연어 → 정형 JSON + query_text

2️⃣ Retriever (Hybrid)
	•	Vector: cosine top-K
	•	BM25/SPLADE: 키워드 매칭
	•	Score blending: final = α*cos + (1-α)*bm25 (기본 α=0.6)
	•	Hard constraints (직군, 지역 등): RDB WHERE 절

3️⃣ AI as Judge (Gemini Flash)
→ 상위 8~12명 병렬 평가, 근거 생성(구어체)

4️⃣ ProfileCard Assembler
→ 상위 4명 RDB 조회, JSONB(custom_data) 포함해 출력

⸻

3.2 Latency 예산 (Gemini API 기준)

모드	구성	평균 응답시간
Speed	Flash only	2.2–3.5s
Balanced	Flash 중심	3.5–5.0s
Quality	Flash + Judge 강화	4–6s


⸻

3.3 다양성 & 품질
	•	MMR (Maximal Marginal Relevance) → 중복 억제
	•	RRF (Reciprocal Rank Fusion) → 여러 랭킹 융합
	•	Hybrid Retrieval 후 Top 8~12만 Judge → 품질/속도 균형

⸻

4. 프롬프트 & 출력 규격

4.1 Persona Prompt
	•	목표: 사용자 raw → persona JSON
	•	모델: Gemini 1.5 Flash (JSON 모드)

4.2 Judge Prompt

{
  "candidate_id": "cand_123",
  "fit_score": 88,
  "reason_ko": "FPGA 기반 딥러닝 가속 경험이 있어, 우리 조직의 H/W PoC를 빠르게 현실화할 수 있는 이유로 추천드려요.",
  "evidence": [
    {"type":"paper","title":"FPGA Accel for CNN","year":2023,"link":"..."},
    {"type":"project","desc":"산학 PoC: YOLOv5 FPGA 포팅","role":"PI","year":2022}
  ]
}

지침:
	•	“~한 이유로 추천드려요.” 구어체 필수
	•	evidence 최소 2개 (논문/프로젝트/성과)
	•	누락 시 missing_fields 포함

⸻

5. 백엔드 API 설계

5.1 주요 엔드포인트

POST /v1/search
입력:

{ "query_text": "FPGA 연구 경험자 찾기", "org_context": {...} }

출력:

{
  "query_summary": "FPGA 및 AI 가속에 강점",
  "candidates_top4": [
    { "id": "...", "name": "...", "fit_score": 87, "reason_ko": "...", "custom_data": {...}, "avatar": "..." }
  ],
  "latency_ms": 3120
}

GET /v1/candidates/{id}
→ custom_data 전체 반환 (직군별 상세 템플릿 대응)

POST /v1/upload/profile
→ GCS pre-signed URL 발급

POST /v1/messages/compose
→ Gemini로 메시지 초안 생성

⸻

5.2 에러 모델

{ "error": { "code": "RATE_LIMIT", "message": "...", "retry_after_ms": 2000 } }


⸻

6. 구현 스켈레톤 (FastAPI/async)

디렉터리 구조

app/
  main.py
  api/routes_search.py
  core/config.py
  services/{persona,retrieve,judge,cards}.py
  adapters/{gemini,qdrant,pg,redis_cache}.py
  schemas/{persona,search,candidate,judge}.py
  utils/{scoring,mmr,rrf,backoff}.py

핵심 코드

@router.post("/search")
async def search(req: dict):
    persona = await build_persona(req)
    initial = await hybrid_retrieve(persona)
    topK = initial[:12]
    judged = await judge_parallel(topK, persona)
    final4 = sorted(judged, key=lambda x: x["fit_score"], reverse=True)[:4]
    cards = await load_cards([c["candidate_id"] for c in final4])
    return {
        "query_summary": persona["persona"]["query_text"],
        "candidates_top4": [
            { **cards[c["candidate_id"]],
              "fit_score": c["fit_score"],
              "reason_ko": c["reason_ko"],
              "custom_data": cards[c["candidate_id"]]["custom_data"] }
            for c in final4
        ]
    }


⸻

7. 클라우드 설정 (GCP 중심)
	•	Google AI Studio / Vertex AI (Gemini API)
	•	Cloud SQL for PostgreSQL (pgvector + JSONB 활성화)
	•	Qdrant Cloud (또는 자체 GKE Qdrant)
	•	GCS 버킷 (파일, 마크다운 저장)
	•	Secret Manager: GEMINI_API_KEY, DB_DSN, REDIS_URL

⸻

8. 성능 최적화 & 캐싱
	•	Judge 병렬 12개
	•	Query→Persona 5–15분 TTL
	•	Persona→Embedding 24시간 TTL

⸻

9. 보안·프라이버시·정책
	•	공개 정보 우선 수집, 민감 데이터 분리
	•	직군별 custom_data 접근 제어
	•	감사 로깅(search_audit)
	•	편향 방지(금지 속성 필터링)
	•	근거는 DB/문헌 링크 필수

⸻



14. 로드맵

1️⃣ MVP: Flash 기반 Hybrid Search
2️⃣ Phase 2: 조직선택, 메시지 작성, 프로필 업로드
3️⃣ Phase 3: Graph Embedding + ColBERT
4️⃣ Phase 4: A/B 테스트, Explainability Dashboard

⸻

15. 부록 – 코드 스니펫

15.1 Persona Builder

async def gemini_flash_json(prompt, schema):
    model = genai.GenerativeModel("gemini-1.5-flash")
    resp = await model.generate_content_async(
        [prompt],
        generation_config={"response_mime_type": "application/json"}
    )
    return resp.text

15.2 Hybrid Retrieve

async def hybrid_retrieve(persona):
    vec = await embed_query(persona["persona"]["query_text"])
    vec_top = await vector_topk(vec, k=50)
    kw_top = await db_keyword_topk(persona, k=50)
    merged = blend_scores(vec_top, kw_top, alpha=0.6)
    cut = apply_hard_constraints(merged, persona)
    diverse = mmr(cut, lambda x: x["vector"], k=12)
    return diverse

15.3 Judge 병렬 호출

async def judge_parallel(cands, persona, batch=8):
    out = []
    for i in range(0, len(cands), batch):
        res = await asyncio.gather(*[
            gemini_flash_json({"persona": persona["persona"], "candidate": c}, "JudgeSchema")
            for c in cands[i:i+batch]
        ])
        out.extend(res)
    return out


⸻

16. 결론
	•	본 문서는 범용 JSON 확장형 인재 스키마를 반영하여
모든 직군(교수, 마케터, 엔지니어, 운동선수 등)을 지원한다.
	•	정형 필드는 검색 효율을, JSONB는 표현 유연성을 담당한다.
	•	Gemini API 기반 LLM + Hybrid Retrieval + AI Judge를 통해
2–5초 이내의 고품질 추천 결과를 제공한다.
	•	구조적 확장성