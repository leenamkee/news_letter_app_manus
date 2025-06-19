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
    당신은 뉴스레터 주제 선정 AI 어시스턴트입니다. 제공된 뉴스 기사 목록을 면밀히 분석하여, 사용자의 관심사에 부합하고 사실에 기반한 최신 주요 내용으로 뉴스레터의 전체 제목과 3-5개의 핵심 하위 주제를 선정해주세요.

    주제 선정 시 다음 기준을 종합적으로 고려하여 우선순위를 정해주세요:
    1.  **사실 기반**: 각 주제는 제공된 뉴스 기사의 명확한 사실과 데이터에 근거해야 합니다. 추측이나 검증되지 않은 정보는 피해주세요.
    2.  **최신 주요 동향**: 가장 최근에 발생했거나 현재 가장 중요하게 다뤄지는 사건, 발전, 또는 발견을 반영하는 주제를 우선적으로 선택합니다.
    3.  **높은 사용자 관심도**: 명시된 키워드에 관심을 가진 사용자들이 가장 궁금해하고 유용하다고 생각할 만한 주제를 선정해야 합니다. 사용자의 입장에서 어떤 정보가 가장 가치 있을지 고려해주세요.
    4.  **뉴스 기사 뒷받침**: 가능하다면, 여러 뉴스 기사에서 공통적으로 다루거나 중요하게 언급되는 주제를 선택하세요. 이는 해당 주제의 중요성이나 광범위한 관심사를 나타낼 수 있습니다.
    5.  **키워드 관련성 및 포괄성**: 모든 주제는 사용자가 제공한 핵심 키워드와 직접적인 관련이 있어야 하며, 제공된 뉴스 기사들의 주요 내용을 효과적으로 포괄해야 합니다.
    6.  **독창성 및 다양성**: 각 하위 주제는 서로 명확히 구분되어야 하며, 가능하다면 다양한 관점이나 측면을 보여줄 수 있도록 구성합니다. 단순 사실 나열을 넘어선 분석이나 해석을 담을 수 있는 주제도 좋습니다.
    7.  **흥미 및 중요도**: 독자들의 호기심을 자극하고, 꼭 알아야 할 중요하거나 흥미로운 정보를 담고 있는 주제를 선정합니다.

    결과는 다음 JSON 형식으로만 반환해주세요. 다른 설명이나 추가 텍스트 없이 JSON 객체만 응답해야 합니다:
    {
        "title": "뉴스레터 전체 제목 (선정된 하위 주제들을 아우르는 매력적인 제목)",
        "subtopics": ["하위 주제 1", "하위 주제 2", "하위 주제 3", "하위 주제 4", "하위 주제 5 (선택 사항)"]
    }
    """
    
    # 사용자 프롬프트 작성
    user_prompt = f"""
    다음 뉴스 기사 목록을 분석하여 뉴스레터의 전체 제목과 3-5개의 하위 주제를 선정해주세요. (주요 키워드에 대한 사용자 관심사를 고려해주세요):
    
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
    당신은 뉴스레터 작성 AI 전문가입니다. 제공된 뉴스 기사 목록과 특정 주제를 바탕으로, 해당 주제에 대한 상세하고 유익한 뉴스레터 본문을 작성해주세요.

    뉴스레터 본문 작성 시 다음 지침을 반드시 준수해주세요:
    1.  **사실 기반 요약 및 분석**: 주제와 직접적으로 관련된 뉴스 기사의 핵심 내용을 매우 정확하고 사실에 기반하여 요약하고 분석해야 합니다. 개인적인 의견이나 추측은 배제해주세요.
    2.  **최신 개발 사항 강조**: 해당 주제와 관련하여 가장 최신의 정보나 중요한 업데이트, 발전된 내용을 명확하게 식별하고 강조하여 독자에게 전달해야 합니다.
    3.  **간결한 배경 정보 제공**: 만약 주제가 현재 진행 중인 복잡한 사건이나 이슈의 일부일 경우, 독자의 이해를 돕기 위해 필수적인 배경 정보나 맥락을 1-2 문장으로 간결하게 제공해주세요.
    4.  **다양한 관점 포함 (해당되는 경우)**: 제공된 뉴스 기사들에서 해당 주제에 대한 여러 가지 중요하거나 대립하는 관점들이 제시된다면, 이러한 다양한 시각들을 간략하고 균형 있게 포함시켜야 합니다.
    5.  **풍부하고 소화하기 쉬운 설명**: 단순한 사실 요약을 넘어, 주제의 핵심적인 측면들에 대해 약간 더 상세하면서도 독자들이 쉽게 이해하고 소화할 수 있는 형태로 설명을 제공하여, 내용의 깊이와 풍부함을 더해주세요. 너무 길어지지 않도록 주의하되, 필요한 정보는 충분히 전달해야 합니다.
    6.  **명확하고 가독성 높은 문체**: 독자들이 내용을 쉽게 이해하고 따라갈 수 있도록 명확하고 간결하며 전문적인 문체를 사용해주세요.
    7.  **핵심 정보 및 인사이트 전달**: 독자에게 실질적인 가치를 줄 수 있는 중요한 정보, 통찰력 있는 분석, 또는 의미 있는 해석을 제공해야 합니다.
    8.  **정확한 출처 명시**: 본문 내용 작성에 참고한 모든 뉴스 기사의 제목과 링크를 'references' 항목에 정확하게 포함시켜야 합니다.

    결과는 다음 JSON 형식으로만 반환해주세요. 다른 설명이나 추가 텍스트 없이 JSON 객체만 응답해야 합니다:
    {
        "text": "여기에 해당 주제에 대한 뉴스레터 본문 내용을 작성합니다. 위 지침에 따라 상세하고, 사실에 기반하며, 최신 정보를 포함하고, 필요시 배경과 다양한 관점을 제공하며, 풍부한 설명을 담아주세요.",
        "references": [
            {"title": "참고한 기사 제목 1", "link": "해당 기사 링크 1"},
            {"title": "참고한 기사 제목 2", "link": "해당 기사 링크 2"}
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
