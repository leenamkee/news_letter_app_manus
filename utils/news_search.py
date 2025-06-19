import feedparser
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta, timezone
import time

def search_news_google_rss(keywords, max_articles=15, freshness_days=7):
    """
    구글 RSS를 사용하여 뉴스 검색
    """
    # 키워드 처리
    keywords_list = [keyword.strip() for keyword in keywords.split(',')]
    search_query = '+'.join(keywords_list)
    
    # Google News RSS URL
    # 참고: Google News RSS는 tbs=qdr:d7 (지난 7일) 같은 파라미터를 공식적으로 지원하지 않는 것으로 보임.
    # 따라서, 모든 결과를 가져온 후 발행일 기준으로 필터링합니다.
    rss_url = f"https://news.google.com/rss/search?q={search_query}&hl=ko&gl=KR&ceid=KR:ko"
    
    # RSS 피드 파싱
    feed = feedparser.parse(rss_url)
    
    # 결과 처리
    all_articles = []
    for entry in feed.entries: # 일단 모든 기사를 가져옴
        published_time = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            # feedparser는 UTC 기준으로 struct_time을 제공
            published_time = datetime.fromtimestamp(time.mktime(entry.published_parsed))

        # freshness_days가 None이 아니고, 발행 시간이 있고, 기준 시간보다 오래된 경우 건너뛰기
        if freshness_days is not None and published_time and published_time < (datetime.utcnow() - timedelta(days=freshness_days)):
            continue

        article = {
            'title': entry.title,
            'link': entry.link,
            'published': entry.get('published', '발행일 정보 없음'), # 원본 발행일 문자열
            'description': entry.get('description', '내용 없음')
        }
        all_articles.append(article)
    
    return all_articles[:max_articles] # 필터링된 목록에서 max_articles 만큼 선택

# datetime, timedelta, timezone은 파일 상단에서 이미 import 되어 있어야 합니다.
# 중복 import 제거. datetime 객체들은 이미 상단에서 import 된 것을 사용합니다.

def search_news_naver_api(keywords, client_id=None, client_secret=None, max_articles=15, freshness_days=7):
    """
    네이버 검색 API를 사용하여 뉴스 검색
    실제 사용 시에는 client_id와 client_secret이 필요합니다.
    """
    # 네이버 API 키가 없는 경우 샘플 데이터 반환 (데모용)
    if not client_id or not client_secret:
        return _get_sample_naver_news(keywords, max_articles=max_articles, freshness_days=freshness_days)
    
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
        "display": max_articles,  # 최대 max_articles 개 기사
        "sort": "date"  # 최신순 정렬
    }
    
    # API 요청
    response = requests.get(url, headers=headers, params=params)
    
    # 결과 처리
    if response.status_code == 200:
        result = response.json()
        filtered_articles = []

        cutoff_date_utc = datetime.utcnow() - timedelta(days=freshness_days)
        
        for item in result.get('items', []):
            pub_date_str = item.get('pubDate')
            article_is_fresh = True # 기본적으로 신선하다고 가정

            if freshness_days is not None and pub_date_str:
                try:
                    # 네이버 pubDate 형식: "Mon, 20 May 2024 15:44:00 +0900"
                    # 이 형식은 %z를 사용하여 timezone 정보를 포함하여 파싱 가능
                    article_date_aware = datetime.strptime(pub_date_str, "%a, %d %b %Y %H:%M:%S %z")
                    # UTC로 변환하여 비교 기준 시간과 통일
                    article_date_utc = article_date_aware.astimezone(timezone.utc)

                    if article_date_utc < cutoff_date_utc:
                        article_is_fresh = False
                except ValueError as e:
                    print(f"네이버 뉴스 날짜 파싱 오류: {pub_date_str}, 오류: {e}")
                    # 파싱 실패 시, 일단 포함 (요구사항에 따라 제외할 수도 있음)
                    article_is_fresh = True
            
            if article_is_fresh:
                # HTML 태그 제거
                title = BeautifulSoup(item['title'], 'html.parser').get_text()
                description = BeautifulSoup(item['description'], 'html.parser').get_text()

                article = {
                    'title': title,
                    'link': item['link'],
                    'published': pub_date_str, # 원본 발행일 문자열
                    'description': description
                }
                filtered_articles.append(article)
        
        return filtered_articles # 이미 max_articles 만큼만 가져왔으므로, 추가 슬라이싱 불필요
    else:
        print(f"네이버 API 오류: {response.status_code}")
        return _get_sample_naver_news(keywords, max_articles=max_articles, freshness_days=freshness_days)  # 오류 시 샘플 데이터 반환

def _get_sample_naver_news(keywords, max_articles=10, freshness_days=7): # freshness_days 추가
    """
    네이버 API 키가 없는 경우 사용할 샘플 데이터 생성 (데모용)
    freshness_days는 API 일관성을 위해 추가되었으나, 여기서는 항상 현재 시간 기준으로 뉴스를 생성합니다.
    """
    # 키워드 처리
    keywords_list = [keyword.strip() for keyword in keywords.split(',')]
    
    # 현재 시간 (KST, +0900)
    # Naver API의 pubDate 형식과 유사하게 맞춤
    # timezone 객체를 사용하기 위해 datetime.timezone을 명시적으로 사용하거나,
    # from datetime import timezone 으로 timezone을 직접 import 해야 합니다.
    # 여기서는 상단에 timezone을 import 했으므로 그대로 사용합니다.
    now_kst = datetime.now(timezone(timedelta(hours=9)))
    now_formatted = now_kst.strftime("%a, %d %b %Y %H:%M:%S +0900")
    
    # 샘플 데이터
    sample_news = []
    for i in range(max_articles): # max_articles 만큼 샘플 생성
        keyword = keywords_list[i % len(keywords_list)]
        sample_news.append({
            'title': f"{keyword}에 관한 최신 뉴스 {i+1} (샘플)",
            'link': f"https://example.com/news/{i}",
            'published': now_formatted, # 현재 시간으로 설정된 샘플 발행일
            'description': f"{keyword}에 관한 최신 동향과 분석을 담은 뉴스 기사입니다. 이것은 데모용 샘플 데이터입니다. (freshness_days: {freshness_days})"
        })
    
    return sample_news
