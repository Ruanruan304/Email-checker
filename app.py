import pandas as pd
import streamlit as st
import socket
import smtplib
from email_validator import validate_email
from concurrent.futures import ThreadPoolExecutor

# 页面配置
st.set_page_config(page_title="邮箱可达性验证工具", layout="wide")

# 标题
st.title("📩 邮箱可达性验证（SMTP级检测）")

# 说明
st.warning("""
**注意**：此验证会与目标邮箱服务器建立SMTP连接，但不会实际发送邮件。
可能被某些邮件服务商限制（如微软/Google），建议少量分批检测。
""")

# 文件上传
uploaded_file = st.file_uploader("上传Excel文件", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        email_col = st.selectbox("选择邮箱列", df.columns)
        
        if st.button("开始验证"):
            emails = df[email_col].dropna().unique()
            
            # SMTP验证函数
            def verify_email(email):
                try:
                    # 先验证格式
                    email_info = validate_email(email, check_deliverability=False)
                    domain = email_info.domain
                    
                    # 获取MX记录
                    mx_records = socket.getaddrinfo(domain, None, socket.AF_INET)
                    if not mx_records:
                        return email, False, "无MX记录"
                    
                    # 尝试SMTP连接（模拟但不发邮件）
                    with smtplib.SMTP(mx_records[0][4][0], timeout=10) as server:
                        server.helo('example.com')
                        server.mail('test@example.com')
                        code, _ = server.rcpt(email)
                        if code == 250:
                            return email, True, "可达"
                        else:
                            return email, False, f"SMTP拒绝({code})"
                
                except Exception as e:
                    return email, False, str(e)

            # 多线程验证
            with ThreadPoolExecutor(max_workers=5) as executor:
                results = list(executor.map(verify_email, emails))
            
            # 显示结果
            st.success("验证完成！")
            result_df = pd.DataFrame(results, columns=["邮箱", "是否可达", "详情"])
            st.dataframe(result_df)
            
            # 下载结果
            st.download_button(
                "下载结果",
                result_df.to_csv(index=False).encode('utf-8'),
                "email_verification_results.csv"
            )

    except Exception as e:
        st.error(f"错误: {str(e)}")
