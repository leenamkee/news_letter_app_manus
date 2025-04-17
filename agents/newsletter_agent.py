from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import TypedDict, List, Dict, Any, Optional
import json
import os

# 상태 정의
class AgentState(TypedDict):
    news_articles: List[Dict[str, str]]
    task: str
    topic: Optional[str]
    result: Optional[Dict[str, Any]]
    openai_api_key: str

# 뉴스레터 주제 생성 노드
def generate_topics_node(state: AgentState) -> AgentState:
    """뉴스 기사를 기반으로 뉴스레터 주제와 하위 주제를 생성하는 노드"""
    
    # OpenAI 모델 초기화
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        api_key=state["openai_api_key"]
    )

    # 뉴스 기사 정보 추출
    articles_info = []
    for article in state["news_articles"]:
        articles_info.append({
            "title": article["title"],
            "description": article["description"]
        })
    
    # 시스템 프롬프트 작성
    system_prompt = """
    당신은 뉴스레터 주제 선정 전문가입니다. 제공된 뉴스 기사 목록을 분석하여 
    뉴스레터의 전체 제목과 5-7개의 하위 주제를 선정해주세요.
    
    하위 주제는 다음 조건을 만족해야 합니다:
    1. 키워드와 관련성이 높아야 함
    2. 제공된 뉴스 기사의 내용을 포괄할 수 있어야 함
    3. 서로 중복되지 않고 다양한 관점을 제공해야 함
    4. 독자들이 관심을 가질만한 흥미로운 주제여야 함
    
    결과는 다음 JSON 형식으로 반환해주세요:
    {
        "title": "뉴스레터 전체 제목",
        "subtopics": ["하위 주제 1", "하위 주제 2", "하위 주제 3", "하위 주제 4", "하위 주제 5"]
    }
    """
    
    # 사용자 프롬프트 작성
    user_prompt = f"""
    다음 뉴스 기사 목록을 분석하여 뉴스레터의 전체 제목과 3-5개의 하위 주제를 선정해주세요:
    
    {json.dumps(articles_info, ensure_ascii=False, indent=2)}
    
    JSON 형식으로만 응답해주세요.
    """
    
    # LLM 호출
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    # try:
    #     del os.environ["HTTP_PROXY"]
    #     del os.environ["HTTPS_PROXY"]
    # except :
    #     pass
    response = llm.invoke(messages)
    # os.environ["HTTP_PROXY"] = "http://70.10.15.10:8080"
    # os.environ["HTTPS_PROXY"] = "http://70.10.15.10:8080"

    # JSON 응답 파싱
    try:
        result = json.loads(response.content)
    except:
        # JSON 파싱 실패 시 텍스트에서 JSON 부분만 추출 시도
        content = response.content
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            try:
                result = json.loads(json_str)
            except:
                result = {
                    "title": "주간 뉴스 하이라이트",
                    "subtopics": ["주요 이슈", "산업 동향", "기술 혁신", "경제 전망", "사회 이슈"]
                }
        else:
            result = {
                "title": "주간 뉴스 하이라이트",
                "subtopics": ["주요 이슈", "산업 동향", "기술 혁신", "경제 전망", "사회 이슈"]
            }
    
    # 결과 업데이트
    state["result"] = result
    return state

# 뉴스레터 내용 생성 노드
def generate_content_node(state: AgentState) -> AgentState:
    """특정 주제에 대한 뉴스레터 내용을 생성하는 노드"""
    
    # OpenAI 모델 초기화
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        api_key=state["openai_api_key"]
    )
    # llm = ChatOpenAI(
    #     model="/mnt/models",
    #     openai_api_key="EMPTY",
    #     openai_api_base="http://meta-llama-3-1-70b-instruct-vllm.serving.70-220-152-1.sslip.io/v1",
    #     max_tokens=200,
    #     temperature=0.5
    # )


    # 뉴스 기사 정보 추출
    articles_info = []
    for article in state["news_articles"]:
        articles_info.append({
            "title": article["title"],
            "link": article["link"],
            "description": article["description"]
        })
    
    # 시스템 프롬프트 작성
    system_prompt = """
    당신은 뉴스레터 작성 전문가입니다. 제공된 뉴스 기사 목록과 주제를 바탕으로
    해당 주제에 맞는 뉴스레터 내용을 작성해주세요.
    
    뉴스레터 내용은 다음 조건을 만족해야 합니다:
    1. 주제와 관련된 뉴스 기사의 핵심 내용을 요약하고 분석해야 함
    2. 독자들이 이해하기 쉬운 명확한 문체로 작성되어야 함
    3. 중요한 정보와 인사이트를 제공해야 함
    4. 참고한 뉴스 기사의 출처를 명시해야 함
    
    결과는 다음 JSON 형식으로 반환해주세요:
    {
        "text": "뉴스레터 본문 내용",
        "references": [
            {"title": "참고 기사 제목 1", "link": "참고 기사 링크 1"},
            {"title": "참고 기사 제목 2", "link": "참고 기사 링크 2"}
        ]
    }
    """
    
    # 사용자 프롬프트 작성
    user_prompt = f"""
    다음 주제에 맞는 뉴스레터 내용을 작성해주세요:
    
    주제: {state["topic"]}
    
    참고할 뉴스 기사 목록:
    {json.dumps(articles_info, ensure_ascii=False, indent=2)}
    
    JSON 형식으로만 응답해주세요.
    """
    
    # LLM 호출
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    # try:
    #     del os.environ["HTTP_PROXY"]
    #     del os.environ["HTTPS_PROXY"]
    # except :
    #     pass
    response = llm.invoke(messages)
    
    # JSON 응답 파싱
    try:
        result = json.loads(response.content)
    except:
        # JSON 파싱 실패 시 텍스트에서 JSON 부분만 추출 시도
        content = response.content
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        if json_start >= 0 and json_end > json_start:
            json_str = content[json_start:json_end]
            try:
                result = json.loads(json_str)
            except:
                # 기본 응답 생성
                result = {
                    "text": f"{state['topic']}에 관한 최신 동향과 분석입니다. 이 주제와 관련된 중요한 뉴스와 인사이트를 제공합니다.",
                    "references": [
                        {"title": articles_info[0]["title"], "link": articles_info[0]["link"]}
                    ]
                }
        else:
            # 기본 응답 생성
            result = {
                "text": f"{state['topic']}에 관한 최신 동향과 분석입니다. 이 주제와 관련된 중요한 뉴스와 인사이트를 제공합니다.",
                "references": [
                    {"title": articles_info[0]["title"], "link": articles_info[0]["link"]}
                ]
            }
    
    # 결과 업데이트
    state["result"] = result
    return state

# 라우터 노드
def router(state: AgentState) -> str:
    """태스크에 따라 적절한 노드로 라우팅하는 함수"""
    return state["task"]

# 뉴스레터 에이전트 그래프 생성
def create_newsletter_agent_graph():
    """뉴스레터 생성을 위한 에이전트 그래프 생성"""
    
    # 그래프 초기화
    workflow = StateGraph(AgentState)
    
    # 노드 추가
    workflow.add_node("generate_topics", generate_topics_node)
    workflow.add_node("generate_content", generate_content_node)
    
    # 엣지 추가 (라우터 사용)
    workflow.add_conditional_edges(
        START, # "",
        router,
        {
            "generate_topics": "generate_topics",
            "generate_content": "generate_content"
        }
    )
    
    # 종료 엣지 추가
    workflow.add_edge("generate_topics", END)
    workflow.add_edge("generate_content", END)
    
    # 그래프 컴파일
    return workflow.compile()

# 뉴스레터 에이전트 실행 함수
def run_newsletter_agent(news_articles, task, openai_api_key, topic=None):
    """
    뉴스레터 에이전트를 실행하는 함수
    
    Parameters:
    - news_articles: 뉴스 기사 목록
    - task: 수행할 작업 ("generate_topics" 또는 "generate_content")
    - openai_api_key: OpenAI API 키
    - topic: 주제 (task가 "generate_content"인 경우에만 필요)
    
    Returns:
    - 작업 결과
    """
    # 에이전트 그래프 생성
    agent = create_newsletter_agent_graph()
    
    # 초기 상태 설정
    initial_state = {
        "news_articles": news_articles,
        "task": task,
        "topic": topic,
        "result": None,
        "openai_api_key": openai_api_key
    }
    
    # 에이전트 실행
    result = agent.invoke(initial_state)
    
    # 결과 반환
    return result["result"]
