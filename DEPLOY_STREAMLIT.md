# Streamlit 공개 URL 배포

## 1. GitHub 저장소 생성

GitHub에서 새 Public 저장소를 만듭니다.

추천 이름:

```text
supplement-routine-agent
```

압축을 해제하고 다음 파일과 폴더를 업로드합니다.

```text
app.py
requirements.txt
README.md
submission_outline.md
.gitignore
docs/
data/
```

실제 API 키, `.env`, `.streamlit/secrets.toml`, 데이터베이스 파일은
GitHub에 업로드하지 않습니다.

## 2. Streamlit Community Cloud 연결

1. Streamlit Community Cloud에 GitHub 계정으로 로그인
2. `Create app`
3. Repository: 본인의 `supplement-routine-agent`
4. Branch: `main`
5. Main file path: `app.py`
6. `Advanced settings` 열기

## 3. API 키 등록

Streamlit의 Secrets 입력란에 다음 형식으로 등록합니다.

```toml
OPENAI_API_KEY = "생성한_API_키"
```

키를 Python 코드나 GitHub 파일에 직접 입력하지 않습니다.

## 4. 배포

`Deploy`를 누르면 다음과 비슷한 주소가 생성됩니다.

```text
https://supplement-routine-agent-사용자명.streamlit.app
```

이 주소가 과제에 제출할 Agent URL입니다.

## 5. 제출 전 테스트

- 시크릿 브라우저 창에서도 URL이 열리는지 확인
- 제품 목록을 2개 이상 입력
- `전체 제품 분석하기` 실행
- `하루 복용 시간표 만들기` 실행
- 제품 하나를 추가하고 `새 제품 추가 점검` 실행
- GitHub에 API 키가 노출되지 않았는지 확인
