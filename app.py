import streamlit as st
import requests
import pandas as pd
import time
import os
from dotenv import load_dotenv

# 初始化环境
load_dotenv()

# --- 安全配置区 ---
def get_api_key():
    """安全获取API Key（优先级：环境变量 > secrets > 手动输入）"""
    # 1. 从环境变量获取
    key = os.getenv("HUNTER_API_KEY")
    if key and key.startswith("hunter_"):
        return key
    
    # 2. 从Streamlit Secrets获取
    try:
        key = st.secrets["HUNTER_API_KEY"]
        if key and key.startswith("hunter_"):
            return key
    except:
        pass
    
    # 3. 手动输入
    key = st.text_input(
        "🔑 输入Hunter.io API Key（以'hunter_'开头）", 
        type="password",
        help="获取地址：https://hunter.io/account"
    )
    if key and key.startswith("hunter_"):
        return key
    
    st.error("❌ 无效的API Key格式！请确认密钥以'hunter_'开头")
    st.stop()

API_KEY = get_api_key()

# --- 核心验证函数 ---
def verify_email(email):
    """验证单个邮箱的可达性"""
    try:
        # 发送请求到Hunter.io
        response = requests.get(
            "https://api.hunter.io/v2/email-verifier",
            params={
                "email": email.strip(),
                "api_key": API_KEY
            },
            timeout=10
        )
        
        # 检查HTTP状态码
        if response.status_code == 401:
            return {
                'email': email,
                'valid': False,
                'details': "API Key无效或已过期",
                'response': None
            }
        
        response.raise_for_status()
        data = response.json().get('data', {})
        
        return {
            'email': email,
            'valid': data.get('status') == 'valid',
            'details': f"{data.get('result', 'unknown')} (可信度: {data.get('score', 'N/A')}%)",
            'response': data  # 原始响应用于调试
        }
        
    except Exception as e:
        return {
            'email': email,
            'valid': False,
            'details': f"验证失败: {str(e)}",
            'response': None
        }

# --- Streamlit界面 ---
st.set_page_config(
    page_title="专业邮箱验证工具",
    page_icon="✉️",
    layout="wide"
)
st.title("✉️ 专业邮箱验证（Hunter.io API）")

# 文件上传
uploaded_file = st.file_uploader(
    "上传Excel文件（.xlsx格式）",
    type=["xlsx"],
    help="文件应包含邮箱列，最大支持200MB"
)

if uploaded_file:
    try:
        # 读取Excel文件
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        st.success(f"成功读取文件，共 {len(df)} 条记录")
        
        # 选择邮箱列
        email_col = st.selectbox(
            "选择邮箱列",
            options=df.columns,
            index=0,
            key="email_column"
        )
        
        # 开始验证按钮
        if st.button("🚀 开始验证", type="primary"):
            emails = df[email_col].dropna().astype(str).str.strip().unique()
            
            # 免费版限制50次/月
            if len(emails) > 50:
                st.warning("Hunter.io免费版每月限制50次验证，本次仅验证前50个邮箱")
                emails = emails[:50]
            
            # 验证进度
            progress_bar = st.progress(0)
            status_area = st.empty()
            results = []
            
            for i, email in enumerate(emails):
                # 执行验证
                result = verify_email(email)
                results.append(result)
                
                # 更新进度
                progress = (i + 1) / len(emails)
                progress_bar.progress(progress)
                
                # 实时显示结果
                status_area.markdown(f"""
                **进度**: {i+1}/{len(emails)}  
                **当前邮箱**: `{email}`  
                **状态**: {'✅ 有效' if result['valid'] else '❌ 无效'}  
                **详情**: {result['details']}
                """)
                
                # 遵守API速率限制（免费版1次/秒）
                time.sleep(1.2)
            
            # 显示最终结果
            st.balloons()
            result_df = pd.DataFrame(results)
            
            # 统计信息
            col1, col2 = st.columns(2)
            col1.metric("有效邮箱", result_df['valid'].sum())
            col2.metric("无效邮箱", len(result_df) - result_df['valid'].sum())
            
            # 结果表格
            st.dataframe(
                result_df[['email', 'valid', 'details']],
                height=400,
                use_container_width=True
            )
            
            # 下载按钮
            st.download_button(
                "📥 下载验证结果",
                result_df.to_csv(index=False).encode('utf-8'),
                "邮箱验证结果.csv",
                mime='text/csv'
            )
            
            # 调试信息（可选）
            with st.expander("原始响应数据（调试用）"):
                st.json([r['response'] for r in results if r['response']])
    
    except Exception as e:
        st.error(f"文件处理错误: {str(e)}")

else:
    st.info("请上传Excel文件以开始验证")
