import streamlit as st
import time
from utils.news_search import search_news_google_rss, search_news_naver_api

def search_news(keywords, search_method, naver_client_id=None, naver_client_secret=None, max_articles=15, freshness_days=7):
    """
    키워드를 기반으로 뉴스를 검색하는 함수
    
    Parameters:
    - keywords: 검색할 키워드 (쉼표로 구분된 문자열)
    - search_method: 검색 방법 ("구글 RSS" 또는 "네이버 API")
    - naver_client_id: 네이버 API Client ID (네이버 API 사용 시 필요)
    - naver_client_secret: 네이버 API Client Secret (네이버 API 사용 시 필요)
    - max_articles: 최대 검색할 기사 수
    - freshness_days: 뉴스 검색 시 최신성 필터링 기간 (일 단위)
    
    Returns:
    - 검색된 뉴스 기사 목록
    """
    # 검색 진행 상태 표시
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 키워드 검색 시작
    status_text.text(f"'{keywords}' 키워드로 뉴스 검색 중...")
    progress_bar.progress(10)
    time.sleep(0.5)
    
    try:
        # 검색 방법에 따라 다른 함수 호출
        if search_method == "구글 RSS":
            status_text.text("구글 뉴스 RSS에서 검색 중...")
            progress_bar.progress(30)
            news_articles = search_news_google_rss(keywords, max_articles=max_articles, freshness_days=freshness_days)
        else:  # 네이버 API
            status_text.text("네이버 뉴스 API에서 검색 중...")
            progress_bar.progress(30)
            news_articles = search_news_naver_api(
                keywords, 
                client_id=naver_client_id, 
                client_secret=naver_client_secret,
                max_articles=max_articles,
                freshness_days=freshness_days
            )
        
        # 검색 결과 처리 (최대 기사 수 제한은 news_search 모듈에서 이미 처리됨)
        progress_bar.progress(70)
        status_text.text("검색 결과 처리 중...")
        time.sleep(0.5)
        
        # 검색 완료
        progress_bar.progress(100)
        status_text.text(f"{len(news_articles)}개의 뉴스 기사를 찾았습니다.")
        time.sleep(0.5)
        
        # 상태 표시 제거
        status_text.empty()
        progress_bar.empty()
        
        return news_articles
    
    except Exception as e:
        # 오류 발생 시
        progress_bar.empty()
        status_text.empty()
        st.error(f"뉴스 검색 중 오류가 발생했습니다: {str(e)}")
        return []

def display_news_articles(news_articles):
    """
    검색된 뉴스 기사를 화면에 표시하는 함수
    
    Parameters:
    - news_articles: 표시할 뉴스 기사 목록
    """
    if not news_articles:
        st.warning("표시할 뉴스 기사가 없습니다.")
        return
    
    # 뉴스 기사 목록 표시
    with st.expander("📰 검색된 뉴스 목록", expanded=True):
        # 테이블 형식으로 표시
        st.markdown("""
        <style>
        .news-table {
            width: 100%;
            border-collapse: collapse;
        }
        .news-table th, .news-table td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .news-table tr:hover {
            background-color: #f5f5f5;
        }
        </style>
        <table class="news-table">
            <tr>
                <th>제목</th>
                <th>발행일</th>
            </tr>
        """, unsafe_allow_html=True)
        
        for article in news_articles:
            st.markdown(f"""
            <tr>
                <td><a href="{article['link']}" target="_blank">{article['title']}</a></td>
                <td>{article['published']}</td>
            </tr>
            """, unsafe_allow_html=True)
        
        st.markdown("</table>", unsafe_allow_html=True)
        
        # 상세 내용 표시
        st.markdown("### 기사 상세 내용")
        for i, article in enumerate(news_articles):
            with st.expander(f"{i+1}. {article['title']}"):
                st.markdown(f"**발행일:** {article['published']}")
                st.markdown(f"**링크:** [기사 원문 보기]({article['link']})")
                st.markdown(f"**내용:** {article['description']}")
