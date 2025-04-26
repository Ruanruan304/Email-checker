import streamlit as st
import requests
import pandas as pd
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 获取API Key（优先级：环境变量 > secrets > 手动输入）
API_KEY = (
    os.getenv("HUNTER_API_KEY") 
    or st.secrets.get("HUNTER_API_KEY")
    or st.text_input("🔑 输入Hunter.io API Key", type="password")
)
if not API_KEY:
    st.warning("请提供API Key")
    st.stop()

# 邮箱验证函数
def verify_email(email):
    try:
        response = requests.get(
            "https://api.hunter.io/v2/email-verifier",
            params={"email": email, "api_key": API_KEY},
            timeout=10
        ).json()
        
        data = response.get('data', {})
        return {
            'email': email,
            'valid': data.get('status') == 'valid',
            'details': f"{data.get('result')} (可信度: {data.get('score')}%)"
        }
    except Exception as e:
        return {'email': email, 'valid': False, 'details': str(e)}

# Streamlit界面
st.title("Hunter.io 邮箱验证工具")
uploaded_file = st.file_uploader("上传Excel文件", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    email_col = st.selectbox("选择邮箱列", df.columns)
    
    if st.button("开始验证"):
        emails = df[email_col].dropna().str.strip().unique()
        results = []
        
        with st.status("验证中...", expanded=True) as status:
            for email in emails[:50]:  # 免费版限制50次/月
                result = verify_email(email)
                results.append(result)
                st.write(f"{email} → {'✅' if result['valid'] else '❌'} {result['details']}")
                time.sleep(1)  # 遵守API速率限制
        
        # 显示结果
        result_df = pd.DataFrame(results)
        st.download_button(
            "下载结果",
            result_df.to_csv(index=False),
            "hunter_verification_results.csv"
        )
