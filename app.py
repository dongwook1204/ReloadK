from flask import Flask, request, jsonify, render_template
import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import sys

# Pydantic 모델을 사용하여 LLM 응답의 JSON 스키마 정의
class QuizOutput(BaseModel):
    """LLM이 생성해야 할 퀴즈 및 설명 결과의 스키마."""
    concept_explanation: str = Field(description="주제와 글을 기반으로 새로 작성된 5~7줄의 간결한 핵심 개념 설명 텍스트.")
    application_problem: str = Field(description="개념을 응용한 계산 또는 서술형 문제 텍스트.")
    answer: str = Field(description="응용 문제의 정답.")
    solution: str = Field(description="문제 풀이 과정 및 해설.")

# Flask 앱 설정
app = Flask(__name__)


# app.py 파일에서 이 부분을 찾아, 아래 코드로 정확하게 대체해주세요.

# Gemini 클라이언트 초기화
try:
    if not os.getenv("GEMINI_API_KEY"):
        # 키가 설정되지 않았을 때만 경고 메시지를 출력하고 client를 None으로 설정
        print("❌ WARNING: GEMINI_API_KEY 환경 변수가 설정되지 않았습니다. 서버는 실행되지만, 퀴즈 생성은 실패합니다.", file=sys.stderr)
        client = None 
    else:
        client = genai.Client()
        print("✅ Gemini API 클라이언트 초기화 완료.")

except Exception as e:
    print(f"❌ API 초기화 오류: {e}", file=sys.stderr)
    client = None


@app.route('/')
def home():
    # templates/index.html을 렌더링
    return render_template('index.html')

@app.route('/generate_quiz', methods=['POST'])
def generate_quiz():
    if client is None:
        return jsonify({"status": "error", "message": "서버에 Gemini API 키가 설정되지 않아 퀴즈를 생성할 수 없습니다."}), 500
        
    data = request.get_json()
    topic = data.get('topic')
    text = data.get('text')

    if not topic or not text:
        return jsonify({"status": "error", "message": "주제와 글을 모두 입력해주세요."}), 400
    
    # LLM에 전달할 사용자 프롬프트 구성
    user_prompt = f"""
    당신은 사용자 입력에 기반하여 해당 수학 개념에 대한 심화 설명과 응용 문제를 출제하는 전문 수학 튜터입니다.
    사용자가 제공한 주제와 글을 참고하여 다음 작업을 수행하세요. 글의 내용에서 벗어난 새로운 개념은 추가하지 않습니다.
    
    [주제]: {topic}
    [관련 글]: {text}
    """
    
    try:
        # Gemini API 호출 및 JSON 응답 강제
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=QuizOutput,
            )
        )
        
        # LLM 응답 (JSON 문자열)을 파싱하여 반환
        llm_output = json.loads(response.text)
        
        # 유효성 검사 (선택 사항)
        QuizOutput(**llm_output)

        return jsonify({"status": "success", "payload": llm_output})

    except Exception as e:
        print(f"❌ LLM 호출 중 오류 발생: {e}", file=sys.stderr)
        return jsonify({"status": "error", "message": "콘텐츠 생성 중 서버 오류가 발생했습니다. API 키나 모델을 확인해주세요."}), 500

if __name__ == '__main__':
    # 디버그 모드로 실행하여 코드 변경 시 자동 재시작 지원
    app.run(debug=True)