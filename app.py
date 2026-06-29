import os
import uuid
from datetime import date
from pathlib import Path

import streamlit as st
from agents import Agent, Runner, SQLiteSession, function_tool


APP_TITLE = "영양제 루틴 Agent"
DB_PATH = str(Path(__file__).with_name("supplement_agent_memory.db"))


@function_tool
def get_today() -> str:
    """Return today's calendar date in ISO format."""
    return date.today().isoformat()


AGENT_INSTRUCTIONS = """
당신은 '영양제 루틴 점검 AI'다.

목표:
사용자가 보유한 영양제 제품을 모두 입력하면 각 제품의 라벨 성분과 함량을 기준으로
중복 성분, 복용 시간, 음식과의 관계, 서로 간격이 필요한 조합, 처방약·질환 관련
주의점을 점검하여 현실적인 하루 복용 루틴을 만든다.

이 에이전트는 의사·약사 또는 의료기관을 대체하지 않는다.
진단, 치료, 처방, 처방약 변경을 하지 않는다.

────────────────────────────────────────
1. 분석에 사용할 정보
────────────────────────────────────────
가능하면 다음 정보를 사용한다.

- 사용자의 나이대
- 임신·수유 여부
- 알레르기와 주요 질환
- 복용 중인 처방약·일반약
- 수술 또는 검사를 앞두고 있는지
- 보유 영양제의 정확한 제품명
- 라벨에 적힌 1회 섭취량
- 성분명과 1회 함량
- 라벨 권장 섭취 횟수
- 사용자의 현재 복용 시간
- 식사 시간, 카페인 섭취, 운동 시간
- 복용 목적
- 최근 발생한 이상 반응

제품명만 있고 성분·함량이 없으면 제품의 구성을 추정하지 않는다.
라벨 정보가 불분명하면 '성분표 확인 필요'라고 표시한다.

────────────────────────────────────────
2. 반드시 지킬 안전 원칙
────────────────────────────────────────
- 사용자가 입력한 라벨 권장량을 넘는 복용량을 제시하지 않는다.
- 치료 목적의 고용량 또는 메가도스를 권하지 않는다.
- 처방약을 시작·중단하거나 복용량을 변경하라고 지시하지 않는다.
- '모든 사람에게 안전하다', '반드시 효과가 있다'처럼 단정하지 않는다.
- 건강 상태를 사용자가 말하지 않았다면 추정하지 않는다.
- 근거가 불충분하면 '확인 불가' 또는 '전문가 확인 필요'라고 말한다.
- 여러 제품에 같은 성분이 있으면 제품별 함량과 하루 합계를 가능한 범위에서 계산한다.
- 단위가 다르거나 환산 기준이 불확실하면 임의 환산하지 않는다.
- proprietary blend, 혼합분말처럼 개별 함량이 공개되지 않은 성분은 정확한 합계를 계산하지 않는다.

다음 상황에서는 일반적인 시간표보다 의사 또는 약사 확인을 우선한다.

- 임신 또는 수유
- 미성년자
- 간·신장 질환
- 출혈 질환
- 수술 또는 시술 예정
- 항응고제·항혈소판제
- 갑상선호르몬제
- 항생제
- 면역억제제
- 항경련제
- 여러 처방약의 동시 복용
- 영양제 복용 후 이상 반응 발생
- 성분 함량이 매우 높거나 단위가 불분명한 제품

호흡곤란, 얼굴·입술 부종, 실신, 심한 흉통, 심한 출혈 등 응급 신호가 언급되면
복용 계획을 만들기보다 즉시 응급 의료 도움을 받도록 안내한다.

────────────────────────────────────────
3. 정보가 부족할 때
────────────────────────────────────────
안전하고 유용한 분석에 필수인 정보가 부족하면 한 번에 최대 3개까지만 질문한다.
가장 중요한 순서는 다음과 같다.

1) 제품별 성분명과 1회 함량
2) 복용 중인 약과 주요 질환
3) 임신·수유·수술 예정 여부
4) 라벨 권장량
5) 식사·운동 시간

질문 없이 분석할 수 있는 부분은 먼저 분석하고,
불확실한 항목만 별도로 표시해도 된다.

────────────────────────────────────────
4. 최종 답변 형식
────────────────────────────────────────
정보가 충분하면 반드시 다음 순서로 답한다.

## 1) 한눈에 보는 결론
- 오늘 루틴의 핵심을 3~5문장으로 요약
- 가장 먼저 수정할 점
- 즉시 전문가 확인이 필요한지 여부

## 2) 보유 제품 점검표
각 제품을 표로 정리한다.

열:
- 제품명
- 주요 성분·함량
- 현재 복용법
- 점검 결과
- 조정 이유

점검 결과 표시는 다음 중 하나를 사용한다.
- 그대로 유지 가능
- 시간 조정 권장
- 중복 성분 확인 필요
- 약사·의사 확인 우선
- 라벨 정보 부족

## 3) 중복 성분과 하루 합계
- 동일 성분이 들어 있는 제품들을 묶는다.
- 제품별 함량과 계산 가능한 하루 합계를 표시한다.
- 정확히 계산할 수 없는 이유가 있으면 명시한다.
- 필요성보다 위험을 과장하지 않는다.

## 4) 추천 하루 복용 시간표
사용자의 실제 식사 시간에 맞춰 다음 구간으로 구성한다.

- 기상 직후 또는 공복
- 아침 식사 중·직후
- 점심 식사 중·직후
- 저녁 식사 중·직후
- 취침 전
- 별도 간격이 필요한 항목

각 행에 다음을 포함한다.
- 시간대
- 제품명
- 라벨 기준 섭취량
- 음식과 함께/공복 여부
- 이유
- 다른 제품·약과 필요한 간격

제품을 억지로 모든 시간대에 배치하지 않는다.
한 번에 먹어도 무리가 없는 제품은 사용 편의성을 고려해 묶을 수 있다.

## 5) 같이 먹을 수 있는 조합 / 분리할 조합
- 함께 복용 가능한 조합
- 시간 간격을 두는 편이 안전한 조합
- 약사 확인 전 병용 판단이 어려운 조합
을 구분한다.

## 6) 꼭 확인할 위험 신호
- 처방약·질환·수술 관련 주의사항
- 복용을 중단하고 평가가 필요한 이상 반응
- 라벨에서 다시 확인할 항목

## 7) 실천용 체크리스트
사용자가 오늘 바로 따를 수 있도록 3~7개의 짧은 체크박스 형식으로 정리한다.

────────────────────────────────────────
5. 대화 방식
────────────────────────────────────────
- 한국어로 답한다.
- 제품명은 사용자가 적은 표현을 그대로 유지한다.
- 설명은 실용적이고 간결하게 한다.
- 사용자가 제품을 추가하면 기존 루틴과 비교해 무엇이 달라지는지 설명한다.
- 사용자가 제품을 빼면 중복 성분과 시간표를 다시 계산한다.
- 같은 세션의 이전 대화와 제품 정보를 활용한다.
"""


supplement_agent = Agent(
    name="Supplement Routine Checker",
    instructions=AGENT_INSTRUCTIONS,
    tools=[get_today],
)


def configure_api_key() -> None:
    """Load API key from environment or Streamlit Cloud Secrets."""
    if os.getenv("OPENAI_API_KEY"):
        return

    try:
        key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        key = ""

    if key:
        os.environ["OPENAI_API_KEY"] = str(key)


def build_user_context() -> str:
    return f"""
[사용자 기본 정보]
- 나이대: {st.session_state.get("age_group", "미입력")}
- 임신·수유: {st.session_state.get("pregnancy", "해당 없음 또는 미입력")}
- 주요 질환·알레르기: {st.session_state.get("conditions", "") or "없음 또는 미입력"}
- 복용 중인 처방약·일반약: {st.session_state.get("medications", "") or "없음 또는 미입력"}
- 수술·시술·검사 예정: {st.session_state.get("procedure", "") or "없음 또는 미입력"}
- 복용 목적: {st.session_state.get("goals", "") or "미입력"}
- 아침 식사 시간: {st.session_state.get("breakfast_time", "미입력")}
- 점심 식사 시간: {st.session_state.get("lunch_time", "미입력")}
- 저녁 식사 시간: {st.session_state.get("dinner_time", "미입력")}
- 운동 시간: {st.session_state.get("exercise_time", "") or "미입력"}
- 커피·카페인 섭취: {st.session_state.get("caffeine", "") or "미입력"}
- 최근 이상 반응: {st.session_state.get("symptoms", "") or "없음 또는 미입력"}

[보유 영양제 전체 목록]
{st.session_state.get("products", "") or "미입력"}
"""


def run_agent(user_request: str) -> str:
    configure_api_key()

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY가 설정되지 않았습니다. "
            "Streamlit Cloud의 App settings > Secrets에 키를 등록하세요."
        )

    session = SQLiteSession(st.session_state.session_id, DB_PATH)
    result = Runner.run_sync(
        supplement_agent,
        f"{build_user_context()}\n\n[현재 요청]\n{user_request}",
        session=session,
    )
    return str(result.final_output)


st.set_page_config(page_title=APP_TITLE, page_icon="💊", layout="wide")

if "session_id" not in st.session_state:
    st.session_state.session_id = f"supplement-user-{uuid.uuid4()}"
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("💊 영양제 루틴 Agent")
st.caption(
    "가지고 있는 영양제를 모두 입력하면 중복 성분과 주의사항을 확인하고, "
    "현실적인 하루 복용 시간표를 만들어드립니다."
)

with st.sidebar:
    st.header("1. 건강·생활 정보")

    st.selectbox(
        "나이대",
        ["미입력", "10대", "20대", "30대", "40대", "50대", "60대 이상"],
        key="age_group",
    )

    st.selectbox(
        "임신·수유 여부",
        ["해당 없음", "임신 중", "수유 중", "확인하고 싶지 않음"],
        key="pregnancy",
    )

    st.text_area(
        "주요 질환·알레르기",
        placeholder="예: 갑상선 기능저하증, 견과류 알레르기 / 없으면 '없음'",
        key="conditions",
        height=90,
    )

    st.text_area(
        "복용 중인 처방약·일반약",
        placeholder="예: 레보티록신 50 μg 아침 복용 / 없으면 '없음'",
        key="medications",
        height=90,
    )

    st.text_area(
        "수술·시술·검사 예정",
        placeholder="예: 2주 뒤 치과 수술 / 없으면 '없음'",
        key="procedure",
        height=70,
    )

    st.text_area(
        "복용 목적",
        placeholder="예: 일반 건강관리, 수면, 운동 회복",
        key="goals",
        height=70,
    )

    st.header("2. 생활 시간")
    st.text_input("아침 식사", value="08:00", key="breakfast_time")
    st.text_input("점심 식사", value="12:30", key="lunch_time")
    st.text_input("저녁 식사", value="19:00", key="dinner_time")
    st.text_input("운동 시간", placeholder="예: 평일 20:00", key="exercise_time")
    st.text_input(
        "커피·카페인",
        placeholder="예: 오전 9시 아메리카노 1잔",
        key="caffeine",
    )

    st.text_area(
        "최근 이상 반응",
        placeholder="예: 마그네슘 복용 후 설사 / 없으면 '없음'",
        key="symptoms",
        height=70,
    )

    if st.button("대화와 저장 정보 초기화", use_container_width=True):
        session = SQLiteSession(st.session_state.session_id, DB_PATH)
        session.clear_session_sync()
        st.session_state.messages = []
        st.session_state.session_id = f"supplement-user-{uuid.uuid4()}"
        st.rerun()

st.subheader("3. 가지고 있는 영양제를 모두 입력하세요")

st.info(
    "제품명만 입력하면 정확한 분석이 어렵습니다. 제품별로 라벨의 "
    "성분명·1회 함량·권장 섭취량을 함께 입력하세요."
)

template = """[제품 1]
제품명:
1회 섭취량:
성분과 함량:
라벨 권장 섭취 횟수:
현재 먹는 시간:

[제품 2]
제품명:
1회 섭취량:
성분과 함량:
라벨 권장 섭취 횟수:
현재 먹는 시간:
"""

st.text_area(
    "제품 목록",
    value=st.session_state.get("products", template),
    key="products",
    height=350,
    help="제품 수만큼 같은 형식을 복사해 추가하세요.",
)

col1, col2, col3 = st.columns(3)

with col1:
    analyze_clicked = st.button(
        "전체 제품 분석하기",
        type="primary",
        use_container_width=True,
    )

with col2:
    schedule_clicked = st.button(
        "하루 복용 시간표 만들기",
        use_container_width=True,
    )

with col3:
    add_clicked = st.button(
        "새 제품 추가 점검",
        use_container_width=True,
    )

preset = None

if analyze_clicked:
    preset = (
        "내가 입력한 모든 제품을 분석해줘. 제품별 점검표, 중복 성분과 하루 합계, "
        "주의사항을 먼저 정리하고 정보가 부족하면 가장 중요한 질문을 최대 3개만 해줘."
    )
elif schedule_clicked:
    preset = (
        "입력한 제품 전체를 기준으로 아침·점심·저녁·취침 전 복용 시간표를 만들어줘. "
        "함께 먹을 제품과 간격을 둘 제품도 구분해줘."
    )
elif add_clicked:
    preset = (
        "이전에 분석한 제품 목록과 현재 입력된 목록을 비교해서 새로 추가된 제품이 "
        "기존 루틴에 어떤 영향을 주는지 점검해줘."
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

typed = st.chat_input(
    "예: 멀티비타민과 비타민 D를 같이 먹어도 되는지 확인해줘."
)
prompt = typed or preset

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("제품 성분과 복용 루틴을 점검하는 중입니다..."):
                response = run_agent(prompt)
            st.markdown(response)
        except Exception as exc:
            response = f"실행 중 오류가 발생했습니다: `{exc}`"
            st.error(response)

    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )

st.divider()
st.caption(
    "본 서비스는 교육용 건강정보 도구이며 진단·치료·처방을 제공하지 않습니다. "
    "처방약, 임신·수유, 주요 질환, 수술 예정 또는 이상 반응이 있는 경우 "
    "의사나 약사에게 실제 제품 라벨을 보여주고 확인하세요."
)
