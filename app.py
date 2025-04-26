import streamlit as st
import pandas as pd
import smtplib
import dns.resolver
import time
from email_validator import validate_email

# ============== 配置区 ==============
SMTP_HELO_DOMAIN = "yourdomain.com"  # 改为你的域名（如 example.com）
SMTP_FROM_EMAIL = "verify@yourdomain.com"  # 改为你的验证邮箱
SMTP_TIMEOUT = 10  # 超时时间（秒）

# ============== 页面设置 ==============
st.set_page_config(
    page_title="纯SMTP邮箱验证工具",
    layout="wide",
    page_icon="✉️"
)
st.title("✉️ 纯SMTP邮箱验证工具")

# ============== 核心函数 ==============
def verify_email(email):
    """通过SMTP协议验证邮箱"""
    try:
        # 1. 验证邮箱格式
        email_info = validate_email(email, check_deliverability=False)
        domain = email_info.domain

        # 2. 查询MX记录
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_host = str(mx_records[0].exchange)

        # 3. SMTP握手验证
        with smtplib.SMTP(mx_host, timeout=SMTP_TIMEOUT) as server:
            server.helo(SMTP_HELO_DOMAIN)
            server.mail(SMTP_FROM_EMAIL)
            code, msg = server.rcpt(email)
            if code == 250:
                return True, "验证通过"
            return False, f"服务器拒绝({code})"

    except dns.resolver.NoAnswer:
        return False, "无MX记录"
    except Exception as e:
        return False, f"错误({str(e)})"

# ============== 主程序 ==============
uploaded_file = st.file_uploader("上传Excel文件", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        email_col = st.selectbox("选择邮箱列", df.columns)
        
        if st.button("开始验证"):
            emails = df[email_col].dropna().astype(str).str.strip().unique()
            results = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, email in enumerate(emails):
                valid, details = verify_email(email)
                results.append({"邮箱": email, "有效": valid, "详情": details})
                
                # 更新进度
                progress = (i + 1) / len(emails)
                progress_bar.progress(progress)
                status_text.markdown(f"""
                **进度**: {i+1}/{len(emails)}  
                **当前**: `{email}` → {'✅' if valid else '❌'} {details}
                """)
                
                time.sleep(1)  # 避免触发反爬
            
            # 显示结果
            result_df = pd.DataFrame(results)
            st.success(f"验证完成！有效邮箱: {result_df['有效'].sum()}/{len(result_df)}")
            st.dataframe(result_df)
            
            # 下载结果
            st.download_button(
                "下载结果",
                result_df.to_csv(index=False).encode('utf-8'),
                "邮箱验证结果.csv"
            )
    
    except Exception as e:
        st.error(f"错误: {str(e)}")
else:
    st.info("请上传Excel文件")
