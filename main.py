#!/usr/bin/env python3
"""
Gemini 2.5 Pro를 사용하여 교수 데이터에서 적합한 교수를 검색하는 스크립트
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from google import genai

# .env 파일 로드
load_dotenv()

# Gemini API 키 설정
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY 환경 변수가 설정되지 않았습니다.")

# genai.configure(api_key=GEMINI_API_KEY)

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).parent
PROFESSOR_DATA_DIR = PROJECT_ROOT / "app" / "data" / "professor_record"


def load_professor_data(max_professors: int = None) -> List[Dict[str, Any]]:
    """
    교수 데이터 JSON 파일들을 읽어서 리스트로 반환
    
    Args:
        max_professors: 최대 교수 수 (None이면 모두 로드)
    
    Returns:
        교수 데이터 리스트
    """
    professor_files = sorted(PROFESSOR_DATA_DIR.glob("professor_*.json"))
    
    if max_professors:
        professor_files = professor_files[:max_professors]
    
    professors = []
    for file_path in professor_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                professors.append(data)
        except Exception as e:
            print(f"Warning: {file_path} 로드 실패: {e}")
    
    return professors


def format_professor_data(professors: List[Dict[str, Any]]) -> str:
    """
    교수 데이터를 프롬프트에 포함할 수 있는 텍스트 형식으로 변환
    
    Args:
        professors: 교수 데이터 리스트
    
    Returns:
        포맷된 교수 데이터 문자열
    """
    formatted_text = "=== 교수 데이터 ===\n\n"
    
    for idx, prof in enumerate(professors, 1):
        formatted_text += f"--- 교수 {idx} ---\n"
        formatted_text += f"이름: {prof.get('name', 'N/A')}\n"
        formatted_text += f"이메일: {prof.get('email', 'N/A')}\n"
        formatted_text += f"소개: {prof.get('introduce', 'N/A')}\n"
        
        if prof.get('keywords'):
            formatted_text += f"키워드: {', '.join(prof['keywords'])}\n"
        
        if prof.get('skills'):
            formatted_text += f"기술/능력: {', '.join(prof['skills'])}\n"
        
        # cards 데이터 추가
        if prof.get('cards'):
            formatted_text += "상세 정보:\n"
            for card in prof['cards']:
                card_type = card.get('type', '')
                card_name = card.get('name', '')
                card_data = card.get('data', '')
                
                if card_type == 'text':
                    formatted_text += f"  - {card_name}: {card_data}\n"
                elif card_type == 'table' and isinstance(card_data, list):
                    formatted_text += f"  - {card_name}:\n"
                    for row in card_data:
                        if isinstance(row, dict) and 'cells' in row:
                            for cell in row['cells']:
                                if isinstance(cell, dict):
                                    cell_name = cell.get('name', '')
                                    cell_value = cell.get('value', '')
                                    formatted_text += f"    {cell_name}: {cell_value}\n"
                elif card_type == 'badgeList' and isinstance(card_data, list):
                    formatted_text += f"  - {card_name}:\n"
                    for badge in card_data:
                        if isinstance(badge, dict):
                            badge_name = badge.get('name', '')
                            formatted_text += f"    - {badge_name}\n"
        
        formatted_text += "\n"
    
    return formatted_text


def create_prompt(professors_data: str, user_input: str) -> str:
    """
    Gemini API에 전달할 프롬프트 생성
    
    Args:
        professors_data: 포맷된 교수 데이터 문자열
        user_input: 사용자 검색 요청
    
    Returns:
        완성된 프롬프트
    """
    prompt = f"""다음은 여러 교수의 정보입니다. 사용자의 요청에 가장 적합한 상위 5명의 교수를 찾아주세요.

{professors_data}

사용자 요청: {user_input}

다음 JSON 형식으로 응답해주세요:
{{
  "top_5_professors": [
    {{
      "name": "교수 이름",
      "reason": "선택한 이유 (간단하게)",
      "match_score": 1-10 점수
    }},
    ...
  ]
}}

각 교수의 적합성을 평가할 때 다음을 고려해주세요:
1. 키워드 및 기술/능력과의 일치도
2. 연구 분야 및 소개 내용의 관련성
3. 상세 정보(cards)에서의 관련 내용

반드시 JSON 형식으로만 응답하고, 추가 설명 없이 JSON만 반환해주세요."""
    
    return prompt


def search_professors(user_input: str, max_professors: int = None) -> Dict[str, Any]:
    """
    Gemini 2.5 Pro를 사용하여 교수를 검색
    
    Args:
        user_input: 사용자 검색 요청
        max_professors: 최대 교수 수 (None이면 모두 사용)
    
    Returns:
        검색 결과 딕셔너리
    """
    print(f"\n교수 데이터 로딩 중...")
    professors = load_professor_data(max_professors)
    print(f"총 {len(professors)}명의 교수 데이터를 로드했습니다.")
    
    print(f"\n프롬프트 생성 중...")
    professors_data = format_professor_data(professors)
    
    # Context length 체크 (대략적인 텍스트 길이로 확인)
    prompt = create_prompt(professors_data, user_input)
    print(f"프롬프트 길이: {len(prompt)} 문자")
    
    # 만약 프롬프트가 너무 길면 경고
    if len(prompt) > 1000000:  # 대략 100만 문자 (약 250K 토큰 정도)
        print("Warning: 프롬프트가 매우 깁니다. 교수 수를 줄이는 것을 고려해주세요.")
        if not max_professors:
            print("50명의 교수로 제한하여 다시 시도합니다...")
            return search_professors(user_input, max_professors=50)
    
    print(f"\nGemini 2.5 Pro 모델 호출 중...")
    # Gemini 2.5 Pro 모델 사용
    # 참고: 모델이 없다면 "gemini-2.5-pro" 또는 "gemini-pro"로 변경해주세요
    try:
        model = genai.GenerativeModel("gemini-2.5-pro")
    except Exception:
        # 만약 gemini-2.5-pro가 없다면 gemini-2.5-pro 사용
        print("Warning: gemini-2.5-pro를 찾을 수 없습니다. gemini-2.5-pro를 사용합니다.")
        model = genai.GenerativeModel("gemini-2.5-pro")
    
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "temperature": 0.3,
            }
        )
        
        result_text = response.text.strip()
        
        # JSON 파싱 시도
        try:
            result = json.loads(result_text)
            return result
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 텍스트에서 JSON 추출 시도
            print("Warning: JSON 파싱 실패. 응답 텍스트에서 JSON 추출 시도...")
            # JSON 부분만 추출 (```json ... ``` 또는 {...} 부분)
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return result
            else:
                print(f"응답 텍스트:\n{result_text}")
                raise ValueError("JSON 형식의 응답을 추출할 수 없습니다.")
    
    except Exception as e:
        print(f"Error: Gemini API 호출 실패: {e}")
        raise


def print_results(result: Dict[str, Any]):
    """
    검색 결과를 보기 좋게 출력
    
    Args:
        result: 검색 결과 딕셔너리
    """
    print("\n" + "=" * 60)
    print("검색 결과: Top 5 교수")
    print("=" * 60)
    
    if "top_5_professors" not in result:
        print("Error: 예상치 못한 응답 형식입니다.")
        print(f"응답 내용: {result}")
        return
    
    for idx, prof in enumerate(result["top_5_professors"], 1):
        print(f"\n{idx}. {prof.get('name', 'N/A')}")
        print(f"   적합도 점수: {prof.get('match_score', 'N/A')}/10")
        print(f"   선택 이유: {prof.get('reason', 'N/A')}")
        print("-" * 60)


def main():
    """메인 함수"""
    print("=" * 60)
    print("교수 검색 시스템 (Gemini 2.5 Pro)")
    print("=" * 60)
    
    # 사용자 입력 받기
    print("\n검색할 교수에 대한 요청을 입력해주세요.")
    print("예: '인공지능 잘하는 교수 찾아줘'")
    user_input = input("\n입력: ").strip()
    
    if not user_input:
        print("Error: 입력이 비어있습니다.")
        return
    
    try:
        # 모든 교수 데이터 사용 시도
        result = search_professors(user_input, max_professors=None)
        
        # 결과 출력
        print_results(result)
        
    except Exception as e:
        print(f"\nError: {e}")
        return


if __name__ == "__main__":
    main()

