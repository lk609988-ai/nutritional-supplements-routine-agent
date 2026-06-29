# 영양제 루틴 Agent

사용자가 보유한 영양제 제품을 모두 입력하면 다음을 제공하는
OpenAI Agents SDK 기반 Streamlit 애플리케이션입니다.

- 제품별 성분 및 복용법 점검
- 중복 성분과 계산 가능한 하루 총량 정리
- 아침·점심·저녁·취침 전 복용 시간표
- 함께 먹을 수 있는 조합과 간격이 필요한 조합
- 처방약·질환·수술 관련 전문가 확인 항목
- 새로운 제품 추가 시 기존 루틴과 비교

## 핵심 설계

이 앱은 하나의 전문 Agent가 사용자 건강정보와 제품 전체 목록을
종합적으로 분석합니다. 같은 세션의 대화는 SQLiteSession으로 기억하므로
제품을 추가하거나 제거했을 때 기존 루틴과 비교할 수 있습니다.

의료적 안전을 위해 다음 제한을 적용했습니다.

- 제품명만으로 성분을 추정하지 않음
- 라벨 권장량을 초과하는 용량을 제안하지 않음
- 처방약 변경을 지시하지 않음
- 고위험 상황은 의사 또는 약사 확인을 우선함
- 불분명한 정보는 추정하지 않고 확인 필요로 표시함

## 로컬 실행

Windows PowerShell:

```powershell
cd supplement_routine_agent
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:OPENAI_API_KEY="발급받은_API_키"
streamlit run app.py
```

## 입력 형식

각 제품에 대해 라벨 정보를 입력합니다.

```text
[제품 1]
제품명: 멀티비타민 A
1회 섭취량: 1정
성분과 함량: 비타민 D 10 μg, 아연 8.5 mg, ...
라벨 권장 섭취 횟수: 하루 1회
현재 먹는 시간: 아침 식후
```

제품명만 입력하면 정확한 중복 성분 계산이나 시간표 설계가 어렵습니다.

## 공개 URL 배포

`DEPLOY_STREAMLIT.md`의 순서를 따라 GitHub와 Streamlit Community Cloud에
배포하면 제출용 공개 URL을 만들 수 있습니다.
