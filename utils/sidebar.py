import streamlit as st
import base64
from PIL import Image
import io

def setup_sidebar():
    """
    사이드바 컴포넌트 설정 및 스타일링
    """
    with st.sidebar:
        # 로고 및 타이틀
        st.markdown("""
        <div style='text-align: center;'>
            <h2 style='color: #4A90E2;'>📰 AI 뉴스레터 생성기</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 키워드 입력
        st.subheader("1️⃣ 키워드 입력")
        keywords = st.text_input(
            "뉴스레터 키워드",
            placeholder="예: 인공지능, 기후변화, 경제",
            help="쉼표(,)로 구분하여 여러 키워드를 입력할 수 있습니다."
        )
        
        # 뉴스 검색 방법 선택
        st.subheader("2️⃣ 검색 방법 선택")
        search_method = st.radio(
            "뉴스 검색 방법",
            options=["구글 RSS", "네이버 API"],
            help="구글 RSS는 API 키가 필요 없지만, 네이버 API는 개발자 계정이 필요합니다."
        )
        
        # 네이버 API 키 입력 (조건부 표시)
        if search_method == "네이버 API":
            with st.expander("네이버 API 설정", expanded=False):
                naver_client_id = st.text_input(
                    "Client ID",
                    type="password",
                    help=""
                )
                naver_client_secret = st.text_input(
                    "Client Secret",
                    type="password",
                    help=""
                )
                st.caption("네이버 개발자 센터에서 애플리케이션을 등록하여 API 키를 발급받을 수 있습니다.")
        
        # OpenAI API 키 입력
        st.subheader("3️⃣ OpenAI API 키 입력")
        openai_api_key = st.text_input(
            "OpenAI API 키",
            type="password",
            help="OpenAI API 키가 없다면 https://platform.openai.com에서 발급받을 수 있습니다."
        )
        
        # 고급 설정
        with st.expander("고급 설정", expanded=False):
            model = st.selectbox(
                "OpenAI 모델",
                options=["gpt-4o-mini", "gpt-4o"],
                index=0
            )
            
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="값이 높을수록 더 창의적인 결과가 생성됩니다."
            )
            
            max_articles = st.slider(
                "최대 뉴스 기사 수",
                min_value=5,
                max_value=20,
                value=15,
                step=1
            )
        
        # 뉴스레터 생성 버튼
        st.markdown("---")
        generate_button = st.button(
            "뉴스레터 생성하기",
            type="primary",
            use_container_width=True
        )
        
        # # Buy me a coffee 링크
        # st.markdown("---")
        
        # # 커피 이미지 추가
        # coffee_html = """
        # <div style='text-align: center;'>
        #     <a href='https://www.buymeacoffee.com' target='_blank'>
        #         <img src='https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png' alt='Buy Me A Coffee' style='height: 40px; width: 150px;'>
        #     </a>
        # </div>
        # """
        # st.markdown(coffee_html, unsafe_allow_html=True)
        
        # 앱 정보
        st.markdown("---")
        st.caption("© 2025 AI 뉴스레터 생성기 | Powered by Streamlit & OpenAI")
    
    # API 키 처리: 사용자 입력이 있으면 사용하고, 없으면 secrets.toml에서 가져옴
    final_openai_api_key = openai_api_key if openai_api_key else st.secrets.get("OPENAI_API_KEY", "")
    final_naver_client_id = naver_client_id if 'naver_client_id' in locals() and naver_client_id else st.secrets.get("NAVER_CLIENT_ID", "")
    final_naver_client_secret = naver_client_secret if 'naver_client_secret' in locals() and naver_client_secret else st.secrets.get("NAVER_CLIENT_SECRET", "")
    
    return {
        "keywords": keywords,
        "search_method": search_method,
        "openai_api_key": final_openai_api_key,
        "generate_button": generate_button,
        "model": model if 'model' in locals() else "gpt-4o-mini",
        "temperature": temperature if 'temperature' in locals() else 0.7,
        "max_articles": max_articles if 'max_articles' in locals() else 15,
        "naver_client_id": final_naver_client_id,
        "naver_client_secret": final_naver_client_secret
    }
