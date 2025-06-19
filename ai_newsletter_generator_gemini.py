# -*- coding: utf-8 -*-
# pip install feedparser schedule python-dotenv openai langchain langchain-openai requests
import os
import smtplib
import feedparser
import schedule
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.header import Header
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
import logging

# --- 설정 ---
# .env 파일에서 환경 변수 로드
load_dotenv()



# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# OpenAI API 키 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.error("환경변수에서 OPENAI_API_KEY를 찾을 수 없습니다.")
    exit()

# Gmail 설정
GMAIL_USER = os.getenv("GMAIL_USER") # 보내는 사람 Gmail 주소
GMAIL_PASSWORD = os.getenv("GMAIL_APP_PASSWORD") # Gmail 앱 비밀번호
RECIPIENT_EMAILS = os.getenv("RECIPIENT_EMAILS", "").split(',') # 받는 사람 이메일 주소 (쉼표로 구분)



if not GMAIL_USER or not GMAIL_PASSWORD or not RECIPIENT_EMAILS:
    logging.error("환경변수에서 Gmail 관련 설정(GMAIL_USER, GMAIL_APP_PASSWORD, RECIPIENT_EMAILS)을 확인하세요.")
    exit()

# 데이터 소스 (RSS 피드 URL)
# 필요에 따라 RSS 피드 추가/수정
RSS_FEEDS = {
    "GeekNews_AI": "https://news.hada.io/topic/ai.rss",
    # "PyTorch_Generative_AI": "https://discuss.pytorch.org/c/generative-ai/54.rss", # 예시 URL, 실제 작동하는지 확인 필요
    "Google AI Blog": "https://ai.googleblog.com/feeds/posts/default?alt=rss",
    "OpenAI Blog": "https://openai.com/blog/rss.xml",
    "DeepMind Blog": "https://deepmind.google/blog/rss.xml",
    "TechCrunch AI": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "VentureBeat AI": "https://feeds.feedburner.com/venturebeat/ai",
    # 다른 주요 기술 뉴스 사이트의 AI 섹션 RSS 추가 가능
}

# 뉴스 요약에 사용할 LLM 모델
LLM_MODEL = "gpt-4o-mini" # 또는 "gpt-3.5-turbo" 등

# 뉴스레터 제목
NEWSLETTER_SUBJECT = f"오늘의 AI 동향 뉴스레터 ({datetime.now().strftime('%Y-%m-%d')})"

# 한번에 요약할 최대 기사 수 (API 비용 및 시간 관리)
MAX_ARTICLES_TO_SUMMARIZE = 20

# --- 기능 함수 ---

def fetch_rss_feeds(feed_urls):
    """지정된 RSS 피드 목록에서 최신 뉴스 항목을 가져옵니다."""
    all_entries = []
    logging.info(f"{len(feed_urls)}개의 RSS 피드에서 뉴스 수집 시작...")
    import ssl

    if hasattr(ssl, '_create_unverified_context'):
        ssl._create_default_https_context = ssl._create_unverified_context

    for name, url in feed_urls.items():
        try:
            feed = feedparser.parse(url)
            if feed.bozo: # feedparser가 파싱 오류를 감지했을 때
                 logging.warning(f"'{name}' 피드 파싱 중 문제 발생 (URL: {url}): {feed.bozo_exception}")
                 continue
            logging.info(f"'{name}' 피드에서 {len(feed.entries)}개 항목 수집 완료.")
            for entry in feed.entries:
                # 간단한 정보만 추출 (제목, 링크, 발행일 - 존재할 경우)
                published_time = entry.get('published_parsed') or entry.get('updated_parsed')
                entry_data = {
                    'title': entry.title,
                    'link': entry.link,
                    'published': time.strftime('%Y-%m-%d %H:%M:%S', published_time) if published_time else 'N/A',
                    'source': name
                }
                # 간단한 중복 제거 (제목과 링크 기준) - 더 정교한 방법 필요시 개선
                if not any(e['title'] == entry_data['title'] and e['link'] == entry_data['link'] for e in all_entries):
                     all_entries.append(entry_data)

        except Exception as e:
            logging.error(f"'{name}' 피드 처리 중 오류 발생 (URL: {url}): {e}")
    logging.info(f"총 {len(all_entries)}개의 고유 뉴스 항목 수집 완료.")
    # 최신순으로 정렬 (발행일 기준, 'N/A'는 뒤로)
    all_entries.sort(key=lambda x: x['published'] if x['published'] != 'N/A' else '0000-00-00 00:00:00', reverse=True)
    return all_entries

def summarize_news_with_langchain(articles):
    """Langchain과 OpenAI LLM을 사용하여 뉴스 기사 목록을 요약합니다."""
    if not articles:
        logging.info("요약할 기사가 없습니다.")
        return "요약할 최신 AI 뉴스가 없습니다."

    logging.info(f"{len(articles)}개 기사 요약 시작 (모델: {LLM_MODEL})...")
    try:
        del os.environ['HTTP_PROXY']
        del os.environ['HTTPS_PROXY']
    except:
        pass

    # Langchain 설정
    llm = ChatOpenAI(temperature=0.3, model_name=LLM_MODEL, openai_api_key=OPENAI_API_KEY)


    system_template = """
    당신은 AI 기술 전문 뉴스레터 에디터입니다. 아래 제공된 AI 관련 뉴스를 바탕으로 한국어로 정리된 뉴스레터를 작성해주세요.
    **중요: 뉴스레터의 모든 정보는 제공된 기사 내용에 엄격히 기반해야 하며, 검증 가능한 사실만을 포함하고 가장 최신의 뉴스를 중심으로 다루어야 합니다. 모든 주장은 기사 내용으로 뒷받침되어야 합니다.**

    뉴스레터 요구사항:
    1. 인트로: AI 기술 동향을 간략하게 소개하는 인사말 (2-3문장). 최신 핵심 트렌드를 언급해주세요.
    2. 다음 섹션으로 구성 (필요시 뉴스 내용에 따라 섹션명 및 구성은 유연하게 조정 가능):
       - LLM 모델 최신 동향: 최신 언어 모델 관련 주요 소식 (예: 새로운 모델 출시, 주요 업데이트, 혁신적 연구 결과).
       - AI 에이전트 기술: 자율 에이전트, 멀티모달 에이전트, 도구 사용(tool use) 등 관련 기술의 발전 사항.
       - 주요 AI 기업 소식: 주요 AI 기업들(예: OpenAI, Google DeepMind, Microsoft, Meta AI 등)의 신제품, 주요 연구 발표, 비즈니스 전략 변화 등.
       - AI 프레임워크 및 도구 업데이트: PyTorch, TensorFlow, LangChain, Hugging Face 등 주요 프레임워크 및 개발 도구 관련 중요 업데이트 소식.
    3. 각 섹션에는 가장 중요하고 최신인 뉴스 3-5개를 선별하여 요약합니다. 단순 요약을 넘어, 해당 뉴스가 가지는 의미, **흥미로운 통찰이나 주목할 만한 트렌드를 포함시키되, 이러한 분석이나 통찰은 반드시 원본 기사의 내용에 의해 명확히 뒷받침되어야 합니다.**
    4. 마무리: 오늘의 주요 AI 동향을 간략히 요약하고, 독자들이 주목해야 할 미래 전망이나 짧은 제언을 포함하여 마무리합니다.
    5. 전체 뉴스레터 분량은 한글 1500-2000자 내외로 작성하여 가독성을 높입니다.
    6. 전문적이면서도 AI 분야에 익숙하지 않은 독자도 이해하기 쉬운 명확하고 간결한 한국어로 작성합니다.
    7. HTML 형식으로 작성해야 합니다. 전체 제목은 <h1>, 뉴스레터의 주요 섹션 제목은 <h2>, 각 뉴스 요약의 소제목은 <h3> 태그를 사용해주세요. 각 뉴스 요약 후에는 원문 기사로 연결되는 하이퍼링크를 명확히 포함시켜야 합니다 (예: `<a href='기사링크'>원문보기</a>`).
    8. **정확한 출처 인용은 투명성과 정보 검증에 매우 중요합니다.** 각 뉴스 요약 말미에는 반드시 원문 출처(소스명)와 함께 위에서 언급된 '원문보기' 링크를 제공해야 합니다.
    9. 독자들의 흥미를 유발하고 가독성을 높이기 위해, 내용과 관련된 적절한 이모지(emoji)를 문맥에 맞게 사용해주세요. (예: 🚀💡🔬🤖)
    """

    # 요약 프롬프트 템플릿
    prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", system_template),
            ("human", "다음은 오늘 수집된 AI 관련 뉴스 목록입니다:\n\n{news_list}\n\n위 목록을 바탕으로 한국어 AI 뉴스레터 본문을 작성해주세요. ")
        ]
    )

    # 기사 목록을 문자열로 변환
    news_list_str = ""
    for i, article in enumerate(articles):
        news_list_str += f"{i+1}. 제목: {article['title']}\n   링크: {article['link']}\n   출처: {article['source']}\n\n"


    # Langchain 체인 생성 및 실행
    # RunnablePassthrough를 사용하여 news_list를 딕셔너리 형태로 전달
    # StrOutputParser()를 사용하여 LLM의 출력을 문자열로 파싱
    chain = {"news_list": RunnablePassthrough()} | prompt_template | llm | StrOutputParser()

    try:
        # invoke 메소드에 news_list_str 직접 전달
        summary = chain.invoke(news_list_str)
        logging.info("뉴스 요약 및 뉴스레터 초안 생성 완료.")
        summary = summary.replace("\n","<br>")
        return summary
    except Exception as e:
        logging.error(f"OpenAI API 호출 또는 Langchain 처리 중 오류 발생: {e}")
        return f"뉴스 요약 중 오류가 발생했습니다: {e}"


def send_email(subject, body, recipient_emails):
    """Gmail을 사용하여 이메일을 발송합니다."""
    if not recipient_emails or not recipient_emails[0]:
         logging.warning("수신자 이메일 주소가 설정되지 않아 이메일을 발송할 수 없습니다.")
         return

    msg = MIMEText(body, 'plain', 'utf-8') # 본문을 UTF-8로 인코딩
    msg['Subject'] = Header(subject, 'utf-8') # 제목을 UTF-8로 인코딩
    msg['From'] = GMAIL_USER
    msg['To'] = ", ".join(recipient_emails) # 여러 수신자 처리

    logging.info(f"'{', '.join(recipient_emails)}' 주소로 이메일 발송 시도...")
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(GMAIL_USER, GMAIL_PASSWORD)
            smtp_server.sendmail(GMAIL_USER, recipient_emails, msg.as_string())
        logging.info("이메일 발송 성공!")
    except smtplib.SMTPAuthenticationError:
        # logging.error("Gmail 로그인 실패. 이메일 주소와 앱 비밀번호를 확인하세요.")
        # logging.error("2단계 인증 사용 시 '앱 비밀번호'를 생성하여 사용해야 합니다.")
        print("Gmail 로그인 실패. 이메일 주소와 앱 비밀번호를 확인하세요.")
    except Exception as e:
        # logging.error(f"이메일 발송 중 오류 발생: {e}")
        print(f"이메일 발송 중 오류 발생: {e}")


def create_and_send_newsletter():
    """뉴스 수집, 요약, 이메일 발송 작업을 수행하는 메인 함수"""
    logging.info("AI 뉴스레터 생성 프로세스 시작...")

    # 1. 뉴스 데이터 수집
    news_items = fetch_rss_feeds(RSS_FEEDS)

    # 2. 요약할 기사 선택 (최신 N개)
    articles_to_summarize = news_items[:MAX_ARTICLES_TO_SUMMARIZE]

    # 3. LLM을 이용한 뉴스 요약 및 뉴스레터 본문 생성
    newsletter_body = summarize_news_with_langchain(articles_to_summarize)

    # 4. 이메일 발송
    send_email(NEWSLETTER_SUBJECT, newsletter_body, RECIPIENT_EMAILS)

    logging.info("AI 뉴스레터 생성 및 발송 프로세스 완료.")


# --- 스케줄링 및 실행 ---

if __name__ == "__main__":
    logging.info("AI 뉴스레터 자동 생성 스크립트 시작.")
    logging.info(f"뉴스레터는 매일 지정된 시간에 발송됩니다.")
    logging.info(f"수신자: {', '.join(RECIPIENT_EMAILS)}")


    # 최초 실행 시 한번 즉시 실행 (테스트 및 즉시 확인용)
    logging.info("스크립트 시작 시 1회 즉시 실행합니다...")
    create_and_send_newsletter()
    logging.info("초기 실행 완료. 스케줄 대기 상태로 전환합니다.")

    # 스케줄 설정 (매일 오전 8시에 실행) - 시간은 필요에 따라 변경
    schedule.every().day.at("08:00").do(create_and_send_newsletter)



    while True:
        schedule.run_pending()
        time.sleep(60) # 1분마다 스케줄 확인
