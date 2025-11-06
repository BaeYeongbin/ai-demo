"""
K-12 AI 학습도구 POC - 인터뷰 활동
Streamlit 메인 애플리케이션
"""
import streamlit as st
import json
from llm_service import LLMService


# 페이지 설정
st.set_page_config(
    page_title="AI 인터뷰 학습도구",
    page_icon="🎓",
    layout="wide"
)


# 세션 상태 초기화
def init_session_state():
    """세션 상태 초기화"""
    if 'llm_service' not in st.session_state:
        st.session_state.llm_service = None

    if 'personae' not in st.session_state:
        st.session_state.personae = None

    if 'objectives' not in st.session_state:
        st.session_state.objectives = None

    if 'selected_persona_name' not in st.session_state:
        st.session_state.selected_persona_name = None

    if 'persona_chats' not in st.session_state:
        st.session_state.persona_chats = {}  # {persona_name: [chat_history]}

    if 'student_answers' not in st.session_state:
        st.session_state.student_answers = {}  # 학습 목표별 답안 {objective_title: answer}

    if 'grading_result' not in st.session_state:
        st.session_state.grading_result = None

    if 'show_grading_modal' not in st.session_state:
        st.session_state.show_grading_modal = False

    if 'topic_info' not in st.session_state:
        st.session_state.topic_info = {}


init_session_state()


# LLM 서비스 초기화
if st.session_state.llm_service is None:
    try:
        st.session_state.llm_service = LLMService()
    except Exception as e:
        st.error(f"❌ LLM 서비스 초기화 실패: {str(e)}")
        st.info("환경변수에 OPENAI_API_KEY가 설정되어 있는지 확인해주세요.")


# 메인 제목
st.title("🎓 AI 인터뷰 학습도구")
st.markdown("---")


# 탭 구성
tab1, tab2 = st.tabs(["📝 선생님 모드", "🎓 학생 모드"])


# 탭 1: 선생님 모드 - 주제 입력 및 페르소나/학습목표 생성
with tab1:
    st.header("📝 주제 입력 및 페르소나/학습목표 생성")

    if st.session_state.llm_service is None:
        st.warning("⚠️ LLM 서비스가 초기화되지 않았습니다. 환경변수를 확인해주세요.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("기본 정보")
            topic = st.text_input("주제", placeholder="예: 일제강점기 문화통치")
            subject = st.text_input("과목", placeholder="예: 사회")
            grade_level = st.text_input("학년/연령", placeholder="예: 중2")

        with col2:
            st.subheader("추가 정보 (선택)")
            scope = st.text_area("수업 맥락/범위", placeholder="예: 일제강점기 중 문화통치 중심")
            persona_count = st.number_input("생성할 페르소나 수", min_value=1, max_value=3, value=2)

        if st.button("🚀 페르소나 및 학습목표 생성", type="primary", use_container_width=True):
            if not topic or not subject or not grade_level:
                st.error("주제, 과목, 학년/연령은 필수 입력 항목입니다.")
            else:
                with st.spinner("페르소나 생성 중..."):
                    try:
                        # 주제 정보 저장
                        st.session_state.topic_info = {
                            'topic': topic,
                            'subject': subject,
                            'grade_level': grade_level,
                            'scope': scope
                        }

                        # 페르소나 생성
                        persona_result = st.session_state.llm_service.generate_persona(
                            topic=topic,
                            subject=subject,
                            grade_level=grade_level,
                            scope=scope,
                            n=persona_count
                        )
                        st.session_state.personae = persona_result

                        # 학습 목표 생성
                        objectives_result = st.session_state.llm_service.generate_objectives(
                            topic=topic,
                            subject=subject,
                            grade_level=grade_level
                        )
                        st.session_state.objectives = objectives_result

                        st.success("✅ 페르소나 및 학습목표가 생성되었습니다!")

                    except Exception as e:
                        st.error(f"❌ 생성 실패: {str(e)}")

        # 생성된 페르소나 표시
        if st.session_state.personae:
            st.markdown("---")
            st.subheader("생성된 페르소나")

            if st.session_state.personae.get('status') == 'fallback':
                st.warning(f"⚠️ Fallback 모드: {st.session_state.personae['fallback']['reason']}")
            else:
                for idx, persona in enumerate(st.session_state.personae.get('personae', [])):
                    with st.expander(f"👤 {persona['display_name']} ({persona['role']})"):
                        # 페르소나 설명
                        if persona.get('description'):
                            st.info(f"📝 {persona['description']}")

                        # 페르소나 이미지 표시
                        if persona.get('image_url'):
                            col1, col2 = st.columns([1, 2])
                            with col1:
                                st.image(persona['image_url'], use_container_width=True)
                            with col2:
                                st.write(f"**시대/지역:** {persona['time_place']}")
                                st.write(f"**말투/톤:** {persona['speaking_style']}")
                                st.write(f"**읽기 수준:** {persona['reading_level']}")
                        else:
                            st.write(f"**시대/지역:** {persona['time_place']}")
                            st.write(f"**말투/톤:** {persona['speaking_style']}")
                            st.write(f"**읽기 수준:** {persona['reading_level']}")

                        if persona.get('bias_risks'):
                            st.write(f"**편향 주의점:** {', '.join(persona['bias_risks'])}")

                        if persona.get('safety_notes'):
                            st.info(f"🛡️ {persona['safety_notes']}")

        # 생성된 학습 목표 표시
        if st.session_state.objectives:
            st.markdown("---")
            st.subheader("학습 목표")

            for idx, obj in enumerate(st.session_state.objectives.get('objectives', [])):
                with st.expander(f"🎯 {obj['title']} ({obj['level']})"):
                    st.write(f"**Bloom 분류:** {obj['bloom']}")
                    st.write(f"**목표:** {obj['objective']}")
                    st.write(f"**안내 질문:** {obj['guide_question']}")

                    st.write("**성공 기준:**")
                    for criteria in obj['success_criteria']:
                        st.write(f"  - {criteria}")

                    st.write("**필요한 증거:**")
                    for evidence in obj['required_evidence']:
                        st.write(f"  - {evidence}")

# 탭 2: 학생 모드 (통합)
with tab2:
    st.header("🎓 학생 모드 - 인터뷰 & 답안 작성")

    if st.session_state.llm_service is None:
        st.warning("⚠️ LLM 서비스가 초기화되지 않았습니다. 환경변수를 확인해주세요.")
    elif not st.session_state.personae or not st.session_state.objectives:
        st.warning("⚠️ 먼저 '선생님 모드' 탭에서 페르소나와 학습목표를 생성해주세요.")
    else:
        # 학습 목표 및 답안 작성 섹션
        st.subheader("📋 학습 목표 및 답안 작성")
        st.info("💡 인터뷰를 통해 정보를 수집한 후, 각 학습 목표에 대한 답안을 작성하세요.")

        # 학습 목표별 답안 입력 칸
        objectives_list = st.session_state.objectives.get('objectives', [])
        for idx, obj in enumerate(objectives_list):
            with st.expander(f"📝 {idx+1}. {obj['title']} ({obj['level']})", expanded=True):
                st.markdown(f"**학습 목표:** {obj['objective']}")
                st.caption(f"💬 가이드 질문: {obj['guide_question']}")

                # 답안 입력 칸
                answer_key = obj['title']
                if answer_key not in st.session_state.student_answers:
                    st.session_state.student_answers[answer_key] = ""

                st.session_state.student_answers[answer_key] = st.text_area(
                    f"답안 작성 (목표 {idx+1})",
                    value=st.session_state.student_answers[answer_key],
                    height=150,
                    placeholder="인터뷰에서 얻은 정보를 바탕으로 답안을 작성하세요...",
                    key=f"answer_{idx}",
                    label_visibility="collapsed"
                )

        st.markdown("---")

        # 페르소나 선택 및 인터뷰 섹션
        st.subheader("💬 페르소나 인터뷰")

        # 페르소나 카드 선택 UI
        st.markdown("#### 페르소나 선택")
        personae_list = st.session_state.personae.get('personae', [])

        if personae_list:
            # 페르소나 카드를 3개씩 1줄에 배치
            for row_start in range(0, len(personae_list), 3):
                cols = st.columns(3)
                row_personae = personae_list[row_start:row_start + 3]

                for col_idx, persona in enumerate(row_personae):
                    with cols[col_idx]:
                        # 페르소나 이름으로 초기화
                        persona_name = persona['display_name']
                        if persona_name not in st.session_state.persona_chats:
                            st.session_state.persona_chats[persona_name] = []

                        # 선택 여부에 따라 카드 스타일 변경
                        is_selected = st.session_state.selected_persona_name == persona_name

                        # 카드 컨테이너 (가로 직사각형 레이아웃)
                        with st.container(border=True):
                            # 이미지와 텍스트를 가로로 배치 (황금비율)
                            img_col, text_col = st.columns([1, 1.618])

                            with img_col:
                                # 페르소나 이미지 (작게)
                                if persona.get('image_url'):
                                    st.image(persona['image_url'], use_container_width=True)

                            with text_col:
                                # 페르소나 이름
                                st.markdown(f"**{persona_name}**")

                                # 페르소나 설명 (짧게)
                                if persona.get('description'):
                                    desc = persona['description']
                                    st.caption(desc[:60] + "..." if len(desc) > 60 else desc)

                                # 선택 버튼
                                button_type = "primary" if is_selected else "secondary"
                                if st.button(
                                    "✓" if is_selected else "선택",
                                    key=f"select_{persona_name}",
                                    type=button_type,
                                    use_container_width=True
                                ):
                                    st.session_state.selected_persona_name = persona_name
                                    st.rerun()

            st.markdown("---")

        # 인터뷰 대화 섹션 (선택된 페르소나가 있을 때만 표시)
        if st.session_state.selected_persona_name:
            st.markdown("#### 인터뷰 대화")

            # 선택된 페르소나 정보 가져오기
            selected_persona = next(
                (p for p in personae_list if p['display_name'] == st.session_state.selected_persona_name),
                None
            )

            if selected_persona:
                # 현재 페르소나의 대화 기록 가져오기
                current_chat_history = st.session_state.persona_chats.get(
                    st.session_state.selected_persona_name, []
                )

                # 대화 기록 표시
                chat_container = st.container()
                with chat_container:
                    for chat in current_chat_history:
                        if chat['role'] == 'student':
                            st.chat_message("user").write(chat['content'])
                        else:
                            # 페르소나 응답 표시 (페르소나 이미지를 아바타로)
                            avatar_url = chat.get('avatar_url', None)
                            with st.chat_message("assistant", avatar=avatar_url):
                                # 본문 응답
                                st.write(chat['content'])

                                # 추가 질문 제안 (있는 경우)
                                if chat.get('suggested_followups'):
                                    with st.expander("💡 추가로 고려해볼 질문", expanded=False):
                                        for followup in chat['suggested_followups']:
                                            st.info(followup)

                # 질문 입력
                student_question = st.chat_input("질문을 입력하세요")

                if student_question:
                    # 학생 질문 추가
                    st.session_state.persona_chats[st.session_state.selected_persona_name].append({
                        'role': 'student',
                        'content': student_question
                    })

                    # 인터뷰 응답 생성
                    with st.spinner("응답 생성 중..."):
                        try:
                            # 대화 히스토리 포맷팅
                            chat_history_text = "\n".join([
                                f"{'학생' if c['role'] == 'student' else '페르소나'}: {c['content']}"
                                for c in current_chat_history[-5:]  # 최근 5턴
                            ])

                            response = st.session_state.llm_service.generate_interview_response(
                                persona_card=selected_persona,
                                student_question=student_question,
                                learning_objectives=st.session_state.objectives,
                                chat_history=chat_history_text,
                                reading_level=selected_persona.get('reading_level', '중등')
                            )

                            # 응답을 구조화하여 저장
                            chat_entry = {
                                'role': 'persona',
                                'content': response['utterance']
                            }

                            # 페르소나 이미지 URL 추가
                            if selected_persona.get('image_url'):
                                chat_entry['avatar_url'] = selected_persona['image_url']

                            # 추가 질문 제안이 있으면 추가
                            if response.get('suggested_followups'):
                                chat_entry['suggested_followups'] = response['suggested_followups']

                            st.session_state.persona_chats[st.session_state.selected_persona_name].append(chat_entry)

                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ 응답 생성 실패: {str(e)}")

                # 인터뷰 초기화 버튼
                st.markdown("---")
                col_reset1, col_reset2 = st.columns([3, 1])
                with col_reset2:
                    if st.button("🔄 현재 인터뷰 초기화", type="secondary", use_container_width=True):
                        st.session_state.persona_chats[st.session_state.selected_persona_name] = []
                        st.rerun()
        else:
            st.info("👆 페르소나를 선택하여 인터뷰를 시작하세요.")

        st.markdown("---")

        # 제출 버튼
        submit_col1, submit_col2 = st.columns([3, 1])
        with submit_col2:
            if st.button("📤 답안 제출 및 채점", type="primary", use_container_width=True):
                # 답안이 모두 작성되었는지 확인
                all_answered = all(
                    st.session_state.student_answers.get(obj['title'], '').strip()
                    for obj in objectives_list
                )

                if not all_answered:
                    st.error("❌ 모든 학습 목표에 대한 답안을 작성해주세요.")
                else:
                    # 채점 진행
                    with st.spinner("채점 중..."):
                        try:
                            # 모든 답안을 하나의 텍스트로 합치기
                            combined_answer = "\n\n".join([
                                f"[{obj['title']}]\n{st.session_state.student_answers.get(obj['title'], '')}"
                                for obj in objectives_list
                            ])

                            # 인터뷰 로그 요약 생성 (모든 페르소나와의 대화 합치기)
                            all_chats = []
                            for persona_name, chats in st.session_state.persona_chats.items():
                                for chat in chats:
                                    all_chats.append({
                                        'persona': persona_name,
                                        'role': chat['role'],
                                        'content': chat['content']
                                    })

                            interview_summary = "\n".join([
                                f"[{c['persona']}] {'학생' if c['role'] == 'student' else '페르소나'}: {c['content'][:100]}..."
                                for c in all_chats[-10:]  # 최근 10턴
                            ]) if all_chats else "인터뷰 기록 없음"

                            # 채점
                            grading_result = st.session_state.llm_service.grade_answer(
                                objectives=st.session_state.objectives,
                                student_answer=combined_answer,
                                interview_summary=interview_summary
                            )

                            st.session_state.grading_result = grading_result
                            st.session_state.show_grading_modal = True
                            st.rerun()

                        except Exception as e:
                            st.error(f"❌ 채점 실패: {str(e)}")

        # 채점 결과 모달
        @st.dialog("📊 채점 결과", width="large")
        def show_grading_modal():
            result = st.session_state.grading_result

            # 전체 점수
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("평균 점수", f"{result['weighted_total']['raw']:.2f} / 3.0")
            with col2:
                st.metric("가중 점수", f"{result['weighted_total']['weighted']:.2f}")
            with col3:
                band = result['weighted_total']['band']
                color = {
                    '미달': '🔴',
                    '기본': '🟡',
                    '충족': '🟢',
                    '우수': '🌟'
                }.get(band, '')
                st.metric("평가 등급", f"{color} {band}")

            st.markdown("---")

            # 기준별 점수
            st.subheader("📈 평가 기준별 점수")
            for score in result.get('scores', []):
                with st.expander(f"{score['criterion']}: {score['level']}/3", expanded=False):
                    st.write(f"**근거:** {score['reason']}")
                    st.info(f"💡 **개선 방법:** {score['fix']}")

            # 학습 목표 달성도
            st.subheader("🎯 학습 목표 달성도")
            for alignment in result.get('objective_alignment', []):
                status = "✅" if alignment['met'] else "❌"
                with st.expander(f"{status} {alignment['objective_title']}", expanded=False):
                    if alignment['met']:
                        st.success("목표 달성!")
                        if alignment.get('evidence_spans'):
                            st.write("**근거:**")
                            for evidence in alignment['evidence_spans']:
                                st.write(f"  - {evidence}")
                    else:
                        st.warning(f"**부족한 점:** {alignment['gap']}")

            # 다음 단계
            if result.get('next_steps'):
                st.subheader("🚀 다음 단계")
                for step in result['next_steps']:
                    st.write(f"- {step}")

            # 플래그
            if result.get('flags'):
                st.subheader("⚠️ 주의사항")
                for flag in result['flags']:
                    st.warning(flag)

            # 닫기 버튼
            if st.button("닫기", type="primary", use_container_width=True):
                st.session_state.show_grading_modal = False
                st.rerun()

        # 모달 표시
        if st.session_state.show_grading_modal and st.session_state.grading_result:
            show_grading_modal()


# 푸터
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.9em;'>
    K-12 AI 학습도구 POC v1.0 | Powered by OpenAI GPT-4.1-nano
    </div>
    """,
    unsafe_allow_html=True
)
