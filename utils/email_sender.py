import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st

def send_newsletter_email(recipient_email: str, newsletter_content: str, subject: str) -> bool:
    """
    생성된 뉴스레터를 이메일로 발송하는 함수
    
    Args:
        recipient_email (str): 수신자 이메일 주소
        newsletter_content (str): 뉴스레터 내용 (HTML 형식)
        subject (str): 이메일 제목
        
    Returns:
        bool: 이메일 발송 성공 여부
    """
    try:
        # Gmail SMTP 서버 설정
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        # secrets.toml에서 이메일 설정 로드
        sender_email = st.secrets.get("GMAIL_USER")
        sender_password = st.secrets.get("GMAIL_APP_PASSWORD")
        
        if not sender_email or not sender_password:
            raise ValueError("이메일 설정이 secrets.toml에 없습니다.")
        
        # 이메일 메시지 생성
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = recipient_email
        
        # HTML 형식의 본문 추가
        html_part = MIMEText(newsletter_content, 'html')
        msg.attach(html_part)
        
        # SMTP 서버 연결 및 이메일 발송
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            
        return True
        
    except Exception as e:
        print(f"이메일 발송 중 오류 발생: {str(e)}")
        return False 
