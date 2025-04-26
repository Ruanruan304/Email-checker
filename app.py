import streamlit as st
import requests
import pandas as pd
import time  # 必须显式导入
from dotenv import load_dotenv
import os

# 初始化环境
load_dotenv()

# 安全获取API Key
API_KEY = os.getenv("HUNTER_API_KEY") or st.secrets.get("HUNTER_API_KEY")
if not API_KEY:
    API_KEY = st.text_input("🔑 输入Hunter.io API Key", type="password")
    if not API_KEY:
        st.warning("请提供API Key以继续")
        st.stop()

# 增强版验证函数
def verify_email(email):
    try:
        response = requests.get(
            "https://api.hunter.io/v2/email-verifier",
            params={"email": email, "api_key": API_KEY},
            timeout=10
        )
        response.raise_for_status()  # 自动捕获HTTP错误
        data = response.json().get('data', {})
        
        return {
            'email': email,
            'valid': data.get('status') == 'valid',
            'details': f"{data.get('result', 'N/A')} (可信度: {data.get('score', 'N/A')}%)",
            'raw_data': data  # 保留原始数据用于调试
        }
    except Exception as e:
        return {
            'email': email,
            'valid': False,
            'details': f"验证失败: {str(e)}",
            'raw_data': None
        }

# 界面构建
st.title("Hunter.io 邮箱验证工具")
uploaded_file = st.file_uploader("上传Excel文件 (.xlsx)", type=["xlsx"])

if uploaded_file and API_KEY:
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        email_col = st.selectbox("选择邮箱列", df.columns)
        
        if st.button("🚀 开始验证", type="primary"):
            emails = df[email_col].dropna().astype(str).str.strip().unique()
            if len(emails) > 50:
                st.warning("免费版限制：本次仅验证前50个邮箱")
                emails = emails[:50]
            
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, email in enumerate(emails):
                result = verify_email(email)
                results.append(result)
                
                # 实时更新进度
                progress = (i + 1) / len(emails)
                progress_bar.progress(progress)
                status_text.markdown(f"""
                **进度**: {i+1}/{len(emails)}  
                **当前结果**:  
                `{email}` → {result['details']}
                """)
                
                time.sleep(1)  # 严格遵守API速率限制
            
            # 显示完整结果
            result_df = pd.DataFrame(results)
            st.success(f"验证完成！有效邮箱: {result_df['valid'].sum()}/{len(result_df)}")
            st.dataframe(result_df[['email', 'valid', 'details']])
            
            # 调试用（可选）
            with st.expander("原始数据（调试）"):
                st.json([r['raw_data'] for r in results if r['raw_data']])
                
    except Exception as e:
        st.error(f"文件处理错误: {str(e)}")
