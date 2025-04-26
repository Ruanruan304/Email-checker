import pandas as pd
import streamlit as st
from email_validator import validate_email, EmailNotValidError

# 页面配置
st.set_page_config(
    page_title="批量邮箱检测小工具",
    layout="wide",
    page_icon="📮"
)

# 标题和说明
st.title("📮 批量邮箱检测小工具")
st.markdown("""
<style>
    .st-emotion-cache-1q7spjk {
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# 文件上传区域
uploaded_file = st.file_uploader(
    "👉 请上传Excel文件（.xlsx格式）",
    type=["xlsx"],
    help="请确保文件包含邮箱列且为Excel格式"
)

if uploaded_file is not None:
    try:
        # 读取Excel文件
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        st.success("✅ 文件上传成功！数据预览：")
        st.dataframe(df.head(3))

        # 选择邮箱列
        email_column = st.selectbox(
            "请选择包含邮箱的列",
            options=df.columns,
            index=0
        )

        # 开始检测按钮
        if st.button("🚀 开始验证", type="primary"):
            emails = df[email_column].dropna().astype(str).tolist()
            
            if not emails:
                st.warning("⚠️ 所选列中没有找到邮箱地址")
                st.stop()
            
            st.info(f"🔍 正在验证 {len(emails)} 个邮箱，请稍候...")
            
            # 验证进度和结果展示
            progress_bar = st.progress(0)
            result_container = st.container()
            
            valid_emails = []
            invalid_emails = []
            
            for i, email in enumerate(emails):
                try:
                    # 真实验证（包含MX记录检查）
                    email_info = validate_email(
                        email,
                        check_deliverability=True
                    )
                    valid_emails.append(email_info.normalized)
                    result_container.success(
                        f"{i+1}. ✅ {email} → 有效（规范格式: {email_info.normalized}）"
                    )
                except EmailNotValidError as e:
                    invalid_emails.append(email)
                    result_container.error(
                        f"{i+1}. ❌ {email} → 无效（原因: {str(e)}）"
                    )
                
                progress_bar.progress((i + 1) / len(emails))
            
            # 最终统计结果
            st.balloons()
            col1, col2 = st.columns(2)
            col1.metric("有效邮箱", len(valid_emails), delta_color="normal")
            col2.metric("无效邮箱", len(invalid_emails), delta_color="inverse")
            
            # 提供结果下载
            if valid_emails or invalid_emails:
                result_df = pd.DataFrame({
                    "原始邮箱": emails,
                    "验证状态": ["有效" if e in valid_emails else "无效" for e in emails],
                    "规范格式": [next((v for v in valid_emails if v == e), "") for e in emails]
                })
                
                st.download_button(
                    label="📥 下载验证结果",
                    data=result_df.to_csv(index=False).encode('utf-8'),
                    file_name='邮箱验证结果.csv',
                    mime='text/csv'
                )

    except Exception as e:
        st.error(f"❌ 处理文件时出错: {str(e)}")
else:
    st.info("⏳ 请上传Excel文件开始验证")
