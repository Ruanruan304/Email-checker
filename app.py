# 文件名：app.py

import streamlit as st
import pandas as pd
import smtplib
import time

st.title('批量邮箱检测器')

uploaded_file = st.file_uploader("上传一个包含邮箱列表的Excel文件（.xlsx）", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    
    if 'email' not in df.columns:
        st.error("Excel文件里必须有一列叫 'email'")
    else:
        result = []
        st.info('开始验证中，请稍等...')
        
        for email in df['email']:
            try:
                # 延迟1秒，防止太快被服务器屏蔽
                time.sleep(1)
                
                domain = email.split('@')[-1]
                server = smtplib.SMTP()
                server.set_debuglevel(0)
                server.connect(domain)
                server.quit()
                result.append((email, "有效"))
            except Exception as e:
                result.append((email, "无效"))
        
        result_df = pd.DataFrame(result, columns=['Email', '状态'])
        st.write(result_df)
        
        # 下载结果
        st.download_button(
            label="下载验证结果",
            data=result_df.to_csv(index=False).encode('utf-8'),
            file_name='email_check_result.csv',
            mime='text/csv'
        )
