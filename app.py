import pandas as pd
import streamlit as st
import socket
import smtplib
from email_validator import validate_email, EmailNotValidError
import time

# 页面配置
st.set_page_config(
    page_title="邮箱可达性验证（SMTP调试版）",
    layout="wide",
    page_icon="📩"
)

# 标题和说明
st.title("📩 邮箱可达性验证（SMTP调试版）")
st.warning("""
**操作说明**：
1. 上传包含邮箱的Excel文件（建议先测试3-5个邮箱）
2. 系统将显示实时验证过程和结果
3. 遇到错误请查看右侧日志面板
""")

# 创建日志输出区域
log_container = st.expander("🔍 实时验证日志", expanded=True)
log_output = log_container.empty()

# 文件上传
uploaded_file = st.file_uploader(
    "上传Excel文件（.xlsx格式）",
    type=["xlsx"],
    help="请确保文件大小不超过10MB"
)

def log_message(message):
    """实时输出日志"""
    log_output.markdown(f"`{time.strftime('%H:%M:%S')}` - {message}")

def verify_email(email):
    """增强版邮箱验证函数"""
    try:
        # 格式验证
        email_info = validate_email(email, check_deliverability=False)
        domain = email_info.domain
        log_message(f"开始验证: {email} (域名: {domain})")
        
        # MX记录查询
        try:
            mx_records = socket.getaddrinfo(domain, 25, socket.AF_INET)
            if not mx_records:
                log_message(f"{email} - 无MX记录")
                return email, False, "无MX记录"
            mx_host = mx_records[0][4][0]
            log_message(f"{email} - 找到MX服务器: {mx_host}")
        except socket.gaierror:
            log_message(f"{email} - 域名解析失败")
            return email, False, "域名解析失败"
        
        # SMTP验证
        try:
            with smtplib.SMTP(mx_host, timeout=10) as server:
                server.helo('example.com')
                server.mail('test@example.com')
                code, msg = server.rcpt(email)
                if code == 250:
                    log_message(f"{email} - ✅ 可达 (响应: {code} {msg})")
                    return email, True, "可达"
                else:
                    log_message(f"{email} - ❌ 拒绝 (响应: {code} {msg})")
                    return email, False, f"SMTP拒绝({code})"
        except Exception as e:
            log_message(f"{email} - ❌ SMTP错误: {str(e)}")
            return email, False, str(e)
            
    except EmailNotValidError as e:
        log_message(f"{email} - ❌ 格式无效: {str(e)}")
        return email, False, str(e)
    except Exception as e:
        log_message(f"{email} - ❌ 验证异常: {str(e)}")
        return email, False, str(e)

if uploaded_file is not None:
    try:
        # 读取文件
        log_message("正在读取Excel文件...")
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        log_message(f"成功读取，共 {len(df)} 行数据")
        
        # 选择邮箱列
        email_col = st.selectbox(
            "选择邮箱列",
            options=df.columns,
            index=0,
            key="email_column"
        )
        st.write("数据预览：", df.head(3))
        
        # 开始验证
        if st.button("🚀 开始验证", type="primary"):
            emails = df[email_col].dropna().astype(str).unique()
            if len(emails) > 50:
                st.warning("检测到超过50个邮箱，建议分批验证")
                emails = emails[:50]  # 限制数量
            
            results = []
            progress_bar = st.progress(0)
            
            for i, email in enumerate(emails):
                results.append(verify_email(email))
                progress_bar.progress((i + 1) / len(emails))
            
            # 显示结果
            result_df = pd.DataFrame(
                results,
                columns=["邮箱", "是否可达", "详情"]
            )
            st.success("验证完成！")
            st.dataframe(result_df)
            
            # 下载结果
            st.download_button(
                "📥 下载验证结果",
                result_df.to_csv(index=False).encode('utf-8'),
                "email_verification_results.csv",
                mime='text/csv'
            )
            
    except Exception as e:
        log_message(f"❌ 文件处理错误: {str(e)}")
        st.error(f"文件处理出错: {str(e)}")
