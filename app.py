import streamlit as st
import streamlit_nested_layout
from utils.sidebar import setup_sidebar
from utils.news_display import search_news, display_news_articles
from utils.email_sender import send_newsletter_email
from agents.newsletter_agent import run_newsletter_agent

import os, requests
import logging

# 로깅 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# os.environ['REQUESTS_CA_BUNDLE'] = '/etc/ssl/certs/ca-certificates.crt'
# os.environ['WDM_SSL_VERIFY'] = '0' #Disable SSL
# os.environ["HTTP_PROXY"] = "http://70.10.15.10:8080"
# os.environ["HTTPS_PROXY"] = "http://70.10.15.10:8080"
# os.environ["PYTHONHTTPSVERIFY"] = "0"


# def disable_ssl_verification():
#     from requests.packages.urllib3.exceptions import InsecureRequestWarning
#     requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


#     old_send = requests.Session.send
#     def new_send(self, request, **kwargs):
#         kwargs['verify'] = False
#         return old_send(self, request, **kwargs)
#     requests.Session.send = new_send

# disable_ssl_verification()



st.set_page_config(
    page_title="뉴스레터 생성기",
    page_icon="📰",
    layout="wide"
)

sidebar_config = {
    'generate_button': True,
    'keywords': '인공지능',
    'openai_api_key': st.secrets.get("OPENAI_API_KEY", "EMPTY"),
    'search_method': 'naver',
    'naver_client_id': st.secrets.get("NAVER_CLIENT_ID", ""),
    'naver_client_secret': st.secrets.get("NAVER_CLIENT_SECRET", ""),
    'max_articles': 30,
    'recipient_email': ''  # 이메일 수신자 추가
}

def convert_markdown_to_html(markdown_content: str) -> str:
    """마크다운 형식의 뉴스레터를 HTML 형식으로 변환"""
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            h1 {{ color: #2c3e50; }}
            h2 {{ color: #34495e; }}
            a {{ color: #3498db; }}
            .reference {{ margin-top: 20px; padding-top: 10px; border-top: 1px solid #eee; }}
        </style>
    </head>
    <body>
        {markdown_content.replace('#', '<h1>').replace('##', '<h2>')}
    </body>
    </html>
    """
    return html_content

def main():
    # 앱 제목
    st.title("AI 뉴스레터 생성기 📰")
    
    # 사이드바 설정
    sidebar_config = setup_sidebar()
    
    # 메인 페이지 설정
    if sidebar_config["generate_button"] and sidebar_config["keywords"] and sidebar_config["openai_api_key"]:
        # 키워드 기반 뉴스 검색
        st.subheader("1️⃣ 키워드 기반 뉴스 검색 중...")
        with st.spinner("뉴스 검색 중..."):
            news_articles = search_news(
                keywords=sidebar_config["keywords"],
                search_method=sidebar_config["search_method"],
                naver_client_id=sidebar_config.get("naver_client_id"),
                naver_client_secret=sidebar_config.get("naver_client_secret"),
                max_articles=sidebar_config.get("max_articles", 15)
            )
            
            if news_articles:
                st.success(f"{len(news_articles)}개의 뉴스 기사를 찾았습니다.")
                logger.debug(f"Found {len(news_articles)} news articles")
                
                # 뉴스 목록 표시
                display_news_articles(news_articles)
            else:
                st.error("뉴스 기사를 찾을 수 없습니다. 다른 키워드를 시도해보세요.")
                logger.error("No news articles found")
                return
        
        # LLM을 통한 뉴스레터 생성
        if news_articles:
            st.subheader("2️⃣ AI가 뉴스레터 주제 선정 중...")
            with st.spinner("주제 선정 중..."):
                newsletter_topics = run_newsletter_agent(
                    news_articles=news_articles,
                    task="generate_topics",
                    openai_api_key=sidebar_config["openai_api_key"]
                )
                
                if newsletter_topics:
                    st.success("뉴스레터 주제가 선정되었습니다.")
                    logger.debug(f"Newsletter topics: {newsletter_topics}")
                    
                    # 선정된 주제 표시
                    st.subheader("📌 선정된 뉴스레터 주제")
                    st.markdown(f"**제목: {newsletter_topics['title']}**")
                    
                    st.markdown("### 하위 주제:")
                    for i, topic in enumerate(newsletter_topics['subtopics']):
                        st.markdown(f"**{i+1}. {topic}**")
                else:
                    st.error("뉴스레터 주제 선정에 실패했습니다.")
                    return
            
            # 각 주제별 뉴스레터 내용 생성
            st.subheader("3️⃣ 각 주제별 뉴스레터 내용 생성 중...")
            newsletter_content = {}
            
            for i, topic in enumerate(newsletter_topics['subtopics']):
                with st.spinner(f"'{topic}' 주제 내용 생성 중..."):
                    content = run_newsletter_agent(
                        news_articles=news_articles,
                        task="generate_content",
                        topic=topic,
                        openai_api_key=sidebar_config["openai_api_key"]
                    )
                    
                    if content:
                        newsletter_content[topic] = content
                        st.success(f"'{topic}' 주제 내용이 생성되었습니다.")
                    else:
                        st.warning(f"'{topic}' 주제 내용 생성에 실패했습니다.")
            
            # 최종 뉴스레터 표시
            if newsletter_content:
                st.subheader("4️⃣ 최종 뉴스레터")

				final_newsletter = f"# {newsletter_topics['title']}\n\n"
				title = newsletter_topics['title']
                
                for topic, content in newsletter_content.items():
                    final_newsletter += f"## {topic}\n\n{content['text']}\n\n"
                    final_newsletter += "**참고 기사:**\n"
                    for ref in content['references']:
                        final_newsletter += f"- [{ref['title']}]({ref['link']})\n"
                    final_newsletter += "\n---\n\n"
                
                st.markdown(final_newsletter)
                
                # 이메일 발송 섹션
                st.subheader("5️⃣ 이메일 발송")
                recipient_email = st.text_input("수신자 이메일 주소를 입력하세요:", sidebar_config.get("recipient_email", ""))
                
                if st.button("뉴스레터 이메일 발송"):
                    if recipient_email:
                        with st.spinner("이메일 발송 중..."):
                            # 마크다운을 HTML로 변환
                            html_content = convert_markdown_to_html(final_newsletter)
                            
                            # 이메일 발송
                            if send_newsletter_email(
                                recipient_email=recipient_email,
                                newsletter_content=html_content,
                                subject=title
                            ):
                                st.success("뉴스레터가 성공적으로 발송되었습니다!")
                                logger.info(f"Newsletter sent to {recipient_email}")
                            else:
                                st.error("이메일 발송에 실패했습니다. 이메일 설정을 확인해주세요.")
                                logger.error("Failed to send newsletter email")
                    else:
                        st.error("수신자 이메일 주소를 입력해주세요.")
                
                # 다운로드 버튼
                st.download_button(
                    label="뉴스레터 다운로드 (Markdown)",
                    data=final_newsletter,
                    file_name="newsletter.md",
                    mime="text/markdown"
                )
    elif sidebar_config["generate_button"]:
        if not sidebar_config["keywords"]:
            st.error("키워드를 입력해주세요.")
        if not sidebar_config["openai_api_key"]:
            st.error("OpenAI API 키를 입력해주세요.")
    else:
        st.info("👈 사이드바에서 키워드와 설정을 입력한 후 '뉴스레터 생성하기' 버튼을 클릭하세요.")
        st.image("https://img.freepik.com/free-vector/newsletter-concept-illustration_114360-1495.jpg", width=500)

if __name__ == "__main__":
    main()
