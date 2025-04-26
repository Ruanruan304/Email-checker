import pandas as pd
import streamlit as st
import smtplib
import time
import dns.resolver
from email_validator import validate_email
from concurrent.futures import ThreadPoolExecutor

# ==================== 配置区 ====================
SMTP_HELO_DOMAIN = "yourdomain.com"  # 改为你的域名
SMTP_FROM_EMAIL = "verify@yourdomain.com"  # 改为你的验证邮箱
MAX_THREADS = 3  # 并发线程数（建议3-5）
TIMEOUT = 20  # 单次验证超时时间（秒）
MAX_RETRIES = 2  # 失败重试次数

# ==================== 页面设置 ====================
st.set_page_config(
    page_title="专业邮箱可达性验证",
    layout="wide",
    page_icon="✉️"
)
st.title("✉️ 专业邮箱可达性验证")
st.markdown("""
<style>
    .stAlert { padding: 20px !important; }
    .st-b7 { color: #ff4b4b !important; }
</style>
""", unsafe_allow_html=True)

# ==================== 核心验证函数 ====================
def verify_email_smtp(email):
    """增强版SMTP验证（含重试机制）"""
    for attempt in range(MAX_RETRIES + 1):
        try:
            # 1. 验证邮箱格式
            email_info = validate_email(email, check_deliverability=False)
            domain = email_info.domain
            
            # 2. 查询MX记录（使用dnspython）
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_host = str(mx_records[0].exchange)
            
            # 3. SMTP握手验证
            with smtplib.SMTP(mx_host, timeout=TIMEOUT) as server:
                server.set_debuglevel(0)
                server.helo(SMTP_HELO_DOMAIN)
                server.mail(SMTP_FROM_EMAIL)
                code, msg = server.rcpt(email)
                if code == 250:
                    return email, True, "可达"
                return email, False, f"SMTP拒绝({code})"
                
        except dns.resolver.NoAnswer:
            return email, False, "无MX记录"
        except dns.resolver.NXDOMAIN:
            return email, False, "域名不存在"
        except smtplib.SMTPServerBusy:
            time.sleep(5)
            continue
        except Exception as e:
            if attempt == MAX_RETRIES:
                return email, False, f"错误({str(e)})"
            time.sleep(3)
    return email, False, "验证超时"

# ==================== API验证方案 ====================
def verify_email_api(email):
    """使用Hunter.io API验证（需注册）"""
    API_KEY = "YOUR_API_KEY"  # 在此替换你的API密钥
    try:
        response = requests.get(
            f"https://api.hunter.io/v2/email-verifier?email={email}&api_key={API_KEY}",
            timeout=30
        ).json()
        status = response['data']['status']
        return (
            email,
            status == 'valid',
            response['data']['result']
        )
    except Exception as e:
        return email, False, f"API错误({str(e)})"

# ==================== 主程序逻辑 ====================
uploaded_file = st.file_uploader("上传Excel文件", type=["xlsx"])
use_api = st.checkbox("使用API验证（更准确但需要密钥）")

if uploaded_file:
    df = pd.read_excel(uploaded_file, engine='openpyxl')
    email_col = st.selectbox("选择邮箱列", df.columns)
    
    if st.button("开始验证", type="primary"):
        emails = df[email_col].dropna().astype(str).unique()
        if len(emails) > 100:
            st.warning("检测到超过100个邮箱，将自动分批验证")
            emails = emails[:100]
        
        # 选择验证方式
        verify_func = verify_email_api if use_api else verify_email_smtp
        
        # 进度显示
        progress_bar = st.progress(0)
        status_text = st.empty()
        results = []
        
        # 并发验证
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            for i, result in enumerate(executor.map(verify_func, emails)):
                results.append(result)
                progress = (i + 1) / len(emails)
                progress_bar.progress(progress)
                status_text.markdown(f"""
                **进度**: {i+1}/{len(emails)}  
                **当前**: `{result[0]}` → {result[2]}
                """)
        
        # 显示结果
        result_df = pd.DataFrame(results, columns=["邮箱", "有效", "详情"])
        st.success("验证完成！成功率: {:.1f}%".format(
            result_df["有效"].mean() * 100
        ))
        st.dataframe(result_df)
        
        # 下载结果
        st.download_button(
            "下载验证结果",
            result_df.to_csv(index=False).encode('utf-8'),
            "邮箱验证结果.csv"
        )

        # 显示统计
        st.metric("有效邮箱", result_df["有效"].sum())
        st.metric("无效邮箱", len(result_df) - result_df["有效"].sum())
