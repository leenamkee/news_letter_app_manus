# AI 뉴스레터 생성기 사용 설명서

## 소개

AI 뉴스레터 생성기는 키워드 기반으로 뉴스를 검색하고, OpenAI의 GPT 모델을 활용하여 자동으로 뉴스레터를 생성하는 도구입니다. 

## 목차

1. [필수 요구사항](#필수-요구사항)
2. [Streamlit 앱 버전 사용 방법](#streamlit-앱-버전-사용-방법)
3. [고급 설정](#고급-설정)
4. [문제 해결](#문제-해결)
5. [자주 묻는 질문](#자주-묻는-질문)

## 필수 요구사항

- **OpenAI API 키**: 뉴스레터 생성에 필요합니다. [OpenAI 플랫폼](https://platform.openai.com)에서 발급받을 수 있습니다.
- **인터넷 연결**: 뉴스 검색 및 API 호출을 위해 필요합니다.
- **Python 3.10 이상**: Streamlit 앱 실행을 위해 필요합니다.
- **필수 패키지**: streamlit, langchain, openai, google-api-python-client, langgraph, requests, beautifulsoup4, feedparser


## Streamlit 앱 버전 사용 방법

### 설치 및 실행

1. 필요한 패키지 설치:
   ```bash
   pip install streamlit langchain openai google-api-python-client langgraph requests beautifulsoup4 feedparser
   ```

2. 앱 실행:
   ```bash
   cd newsletter_app
   streamlit run app.py
   ```

3. 웹 브라우저에서 앱 접속:
   ```
   http://localhost:8501
   ```

### 뉴스레터 생성 과정

1. **사이드바 설정**:
   - 키워드 입력: 쉼표(,)로 구분하여 여러 키워드 입력 가능
   - 뉴스 검색 방법 선택: 구글 RSS 또는 네이버 API
   - OpenAI API 키 입력
   - 고급 설정(선택사항): 모델, Temperature, 최대 뉴스 기사 수 설정

2. **뉴스레터 생성 버튼 클릭**:
   - 키워드 기반 뉴스 검색 진행
   - 검색된 뉴스 목록 표시
   - AI가 뉴스레터 주제 선정
   - 각 주제별 뉴스레터 내용 생성
   - 최종 뉴스레터 표시 및 다운로드 옵션 제공

## 고급 설정

### Streamlit 앱 버전

- **OpenAI 모델**: GPT-4o(기본값), GPT-4-turbo, GPT-3.5-turbo 중 선택
- **Temperature**: 0.0(정확성 중시) ~ 1.0(창의성 중시), 기본값 0.7
- **최대 뉴스 기사 수**: 5~20개 설정 가능, 기본값 15개

### Google Apps Script 버전

- **OpenAI 모델**: GPT-4o(기본값), GPT-4-turbo, GPT-3.5-turbo 중 선택
- **Temperature**: 0.0~1.0 설정 가능, 기본값 0.7
- **최대 뉴스 기사 수**: 5, 10, 15, 20개 중 선택, 기본값 15개

## 문제 해결

### 공통 문제

1. **뉴스 검색 실패**:
   - 인터넷 연결 확인
   - 다른 키워드 시도
   - 다른 검색 방법 사용

2. **OpenAI API 오류**:
   - API 키 정확성 확인
   - API 사용량 한도 확인
   - 다른 모델 선택

### Streamlit 앱 버전 문제

1. **앱 실행 오류**:
   - 필요한 패키지가 모두 설치되었는지 확인
   - Python 버전 확인(3.10 이상 권장)
   - 오류 메시지 확인 후 필요한 패키지 추가 설치

2. **성능 문제**:
   - 최대 뉴스 기사 수 줄이기
   - 더 가벼운 모델(GPT-3.5-turbo) 사용


## 자주 묻는 질문

**Q: API 키는 어디에 저장되나요?**  
A: Streamlit 앱 버전에서는 세션 내에서만 사용되고 저장되지 않습니다. 

**Q: 뉴스레터 생성에 비용이 드나요?**  
A: OpenAI API 사용에 따른 비용이 발생할 수 있습니다. 사용량에 따라 요금이 부과되므로 OpenAI 가격 정책을 확인하세요.

**Q: 생성된 뉴스레터를 수정할 수 있나요?**  
A: 네, Streamlit 앱 버전에서는 다운로드한 Markdown 파일을 수정할 수 있습니다.

**Q: 다른 언어로 뉴스레터를 생성할 수 있나요?**  
A: 네, 키워드를 원하는 언어로 입력하면 해당 언어로 뉴스를 검색하고 뉴스레터를 생성합니다.
