"""
LLM 서비스 모듈 - OpenAI GPT API 사용
"""
import json
import os
import re

from openai import OpenAI


class LLMService:
    """LLM API 호출을 담당하는 서비스 클래스"""

    def __init__(self):
        """
        LLMService 초기화
        환경변수에서 OpenAI API 키를 가져옴
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")

        # Streamlit Community Cloud 호환성을 위해 명시적으로 초기화
        self.client = OpenAI(
            api_key=self.api_key,
            timeout=60.0,
            max_retries=3
        )
        self.model = "gpt-4.1-nano"

    def _extract_json(self, text):
        """
        텍스트에서 JSON 추출

        Args:
            text: LLM 응답 텍스트

        Returns:
            dict: 파싱된 JSON 객체
        """
        # 먼저 전체 텍스트를 JSON으로 파싱 시도
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # JSON 코드 블록 찾기
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 중괄호로 둘러싸인 부분 찾기
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"유효한 JSON을 찾을 수 없습니다: {text[:200]}")

    def call_llm(self, prompt, max_tokens=4000):
        """
        LLM API 호출

        Args:
            prompt: 프롬프트 텍스트
            max_tokens: 최대 토큰 수

        Returns:
            str: LLM 응답 텍스트
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"LLM API 호출 실패: {str(e)}")

    def call_llm_json(self, prompt, max_tokens=4000):
        """
        LLM API 호출 후 JSON 파싱

        Args:
            prompt: 프롬프트 텍스트
            max_tokens: 최대 토큰 수

        Returns:
            dict: 파싱된 JSON 응답
        """
        response_text = self.call_llm(prompt, max_tokens)
        return self._extract_json(response_text)

    def generate_persona_image(self, persona_info):
        """
        페르소나 이미지 생성 (실존 인물의 경우 역사적 정확성 추구)

        Args:
            persona_info: 페르소나 정보 딕셔너리 (display_name, role, time_place 등)

        Returns:
            str: 생성된 이미지 URL
        """
        try:
            display_name = persona_info.get('display_name', '')
            role = persona_info.get('role', 'a person')
            time_place = persona_info.get('time_place', 'historical period')
            description = persona_info.get('description', '')

            # 실존 인물 여부 확인 (괄호 안에 실명이 있거나 역사적 인물인 경우)
            is_historical_figure = '(' in display_name or any(keyword in role.lower() for keyword in ['king', 'emperor', 'inventor', 'scientist', 'writer', 'poet', '왕', '장군', '의사', '독립운동가'])

            # 한국 역사 인물 여부 확인
            is_korean_historical = any(keyword in time_place for keyword in ['조선', '한국', '고려', '고구려', '백제', '신라', 'Korea', 'Joseon', 'Goryeo'])

            if is_historical_figure:
                if is_korean_historical:
                    # 한국 역사 인물: 한국 전통 복장과 문화 반영
                    image_prompt = f"""A historically accurate portrait illustration of {role} from {time_place}.
Show authentic Korean traditional clothing (hanbok) appropriate to their status and era, with accurate colors and patterns.
Include traditional Korean cultural elements, accessories, and headwear typical of {time_place}.
Based on Korean historical records and traditional portrait paintings (초상화).
Professional educational illustration style with Korean historical accuracy, detailed and respectful.
Suitable for K-12 Korean history education.
Realistic historical Korean portrait style with accurate period details and traditional aesthetics."""
                else:
                    # 일반 역사 인물: 역사적으로 정확한 복장, 시대적 배경, 지위에 맞는 모습
                    image_prompt = f"""A historically accurate portrait illustration of {role} from {time_place}.
Show authentic period-appropriate clothing, accessories, and hairstyle typical of their social status and era.
Include historically accurate details: traditional costume, cultural items, and setting that reflects {time_place}.
Based on historical records and period artwork.
Professional educational illustration style, detailed and respectful, suitable for K-12 history education.
Realistic historical portrait style with accurate period details."""
            else:
                # 일반 페르소나: 직업과 시대에 맞는 일러스트레이션
                image_prompt = f"""A portrait illustration of {role} from {time_place}.
{description if description else 'Show professional attire and setting appropriate to their role.'}
Professional educational illustration style, neutral background, suitable for K-12 education.
Clean, modern illustration style."""

            response = self.client.images.generate(
                model="dall-e-3",
                prompt=image_prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )

            return response.data[0].url
        except Exception as e:
            print(f"이미지 생성 실패: {str(e)}")
            return None

    def generate_persona(self, topic, subject, grade_level, scope="",
                        disallowed="없음", allowed_sources="",
                        persona_style="", n=2):
        """
        페르소나 생성 (이미지 포함)

        Args:
            topic: 주제
            subject: 과목
            grade_level: 학년/연령
            scope: 수업 맥락/범위
            disallowed: 금지 요소
            allowed_sources: 지식 소스
            persona_style: 페르소나 스타일
            n: 생성할 페르소나 수

        Returns:
            dict: 페르소나 정보 (이미지 URL 포함)
        """
        from prompts import format_persona_prompt

        prompt = format_persona_prompt(
            topic=topic,
            subject=subject,
            grade_level=grade_level,
            scope=scope,
            disallowed=disallowed,
            allowed_sources=allowed_sources,
            persona_style=persona_style,
            n=n
        )

        result = self.call_llm_json(prompt)

        # 각 페르소나에 대해 이미지 생성
        if result.get('status') == 'ok' and result.get('personae'):
            for persona in result['personae']:
                image_url = self.generate_persona_image(persona)
                persona['image_url'] = image_url

        return result

    def generate_objectives(self, topic, subject, grade_level,
                           duration_and_scope="45분, 인터뷰 10턴 후 서술문 400자",
                           prior_knowledge="", focus="", disallowed="없음"):
        """
        학습 목표 질문 생성

        Args:
            topic: 주제
            subject: 과목
            grade_level: 학년/연령
            duration_and_scope: 수업 길이/활동 범위
            prior_knowledge: 선수지식
            focus: 평가 포커스
            disallowed: 금지 요소

        Returns:
            dict: 학습 목표 정보
        """
        from prompts import format_objectives_prompt

        prompt = format_objectives_prompt(
            topic=topic,
            subject=subject,
            grade_level=grade_level,
            duration_and_scope=duration_and_scope,
            prior_knowledge=prior_knowledge,
            focus=focus,
            disallowed=disallowed
        )

        return self.call_llm_json(prompt)

    def generate_interview_response(self, persona_card, student_question,
                                   learning_objectives=None, chat_history="",
                                   reading_level="중등", disallowed="없음"):
        """
        인터뷰 응답 생성

        Args:
            persona_card: 페르소나 카드 정보 (dict)
            student_question: 학생 질문
            learning_objectives: 학습 목표 정보 (dict) - 학생 학습 유도용
            chat_history: 대화 히스토리
            reading_level: 읽기 난이도
            disallowed: 금지 요소

        Returns:
            dict: 인터뷰 응답 정보
        """
        from prompts import format_interview_prompt

        # 학습 목표를 텍스트로 포맷팅
        learning_objectives_text = ""
        if learning_objectives and learning_objectives.get('objectives'):
            objectives_list = []
            for obj in learning_objectives['objectives']:
                objectives_list.append(f"- {obj['title']}: {obj['guide_question']}")
            learning_objectives_text = "\n".join(objectives_list)

        prompt = format_interview_prompt(
            persona_card_json=json.dumps(persona_card, ensure_ascii=False, indent=2),
            student_question=student_question,
            learning_objectives=learning_objectives_text,
            chat_history=chat_history,
            reading_level=reading_level,
            disallowed=disallowed
        )

        # 500자 이내 응답을 위해 max_tokens를 2000으로 설정
        return self.call_llm_json(prompt, max_tokens=2000)

    def grade_answer(self, objectives, student_answer, interview_summary="",
                    weights="", originality_rules=""):
        """
        답안 채점

        Args:
            objectives: 학습 목표 (dict)
            student_answer: 학생 최종 답안
            interview_summary: 인터뷰 로그 요약
            weights: 교사 가중치
            originality_rules: 표절/AI 작성 의심 규칙

        Returns:
            dict: 채점 결과
        """
        from prompts import format_grading_prompt

        prompt = format_grading_prompt(
            objectives_json=json.dumps(objectives, ensure_ascii=False, indent=2),
            student_answer=student_answer,
            interview_summary=interview_summary,
            weights=weights,
            originality_rules=originality_rules
        )

        return self.call_llm_json(prompt)
