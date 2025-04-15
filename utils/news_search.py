import feedparser
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time

def search_news_google_rss(keywords):
    """
    구글 RSS를 사용하여 뉴스 검색
    """
    # 키워드 처리
    keywords_list = [keyword.strip() for keyword in keywords.split(',')]
    search_query = '+'.join(keywords_list)
    
    # Google News RSS URL
    rss_url = f"https://news.google.com/rss/search?q={search_query}&hl=ko&gl=KR&ceid=KR:ko"
    
    # RSS 피드 파싱
    feed = feedparser.parse(rss_url)
    
    # 결과 처리
    news_articles = []
    for entry in feed.entries[:15]:  # 최대 15개 기사만 가져옴
        article = {
            'title': entry.title,
            'link': entry.link,
            'published': entry.published,
            'description': entry.get('description', '내용 없음')
        }
        news_articles.append(article)
    
    return news_articles

def search_news_naver_api(keywords, client_id=None, client_secret=None):
    """
    네이버 검색 API를 사용하여 뉴스 검색
    실제 사용 시에는 client_id와 client_secret이 필요합니다.
    """
    # 네이버 API 키가 없는 경우 샘플 데이터 반환 (데모용)
    if not client_id or not client_secret:
        return _get_sample_naver_news(keywords)
    
    # 키워드 처리
    keywords_list = [keyword.strip() for keyword in keywords.split(',')]
    search_query = ' '.join(keywords_list)
    
    # 네이버 검색 API URL
    url = "https://openapi.naver.com/v1/search/news.json"
    
    # 헤더 설정
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret
    }
    
    # 파라미터 설정
    params = {
        "query": search_query,
        "display": 15,  # 최대 15개 기사
        "sort": "date"  # 최신순 정렬
    }
    
    # API 요청
    response = requests.get(url, headers=headers, params=params)
    
    # 결과 처리
    if response.status_code == 200:
        result = response.json()
        news_articles = []
        
        for item in result.get('items', []):
            # HTML 태그 제거
            title = BeautifulSoup(item['title'], 'html.parser').get_text()
            description = BeautifulSoup(item['description'], 'html.parser').get_text()
            
            article = {
                'title': title,
                'link': item['link'],
                'published': item['pubDate'],
                'description': description
            }
            news_articles.append(article)
        
        return news_articles
    else:
        print(f"네이버 API 오류: {response.status_code}")
        return _get_sample_naver_news(keywords)  # 오류 시 샘플 데이터 반환

def _get_sample_naver_news(keywords):
    """
    네이버 API 키가 없는 경우 사용할 샘플 데이터 생성 (데모용)
    """
    # 키워드 처리
    keywords_list = [keyword.strip() for keyword in keywords.split(',')]
    
    # 현재 시간
    now = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0900")
    
    # 샘플 데이터
    sample_news = []
    for i in range(10):
        keyword = keywords_list[i % len(keywords_list)]
        sample_news.append({
            'title': f"{keyword}에 관한 최신 뉴스 {i+1}",
            'link': f"https://example.com/news/{i}",
            'published': now,
            'description': f"{keyword}에 관한 최신 동향과 분석을 담은 뉴스 기사입니다. 이것은 데모용 샘플 데이터입니다."
        })
    
    return sample_news
