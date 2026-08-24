import streamlit as st


st.set_page_config(
    page_title="Study Tool",
    page_icon="📚",
    layout="wide"
)

st.title("📚 把教材變成你的測驗")

st.write(
    "上傳你的課堂講義，系統會整理教材內容，並根據重要概念產生測驗。"
)

st.divider()

uploaded_file = st.file_uploader(
    "上傳 PDF",
    type=["pdf"]
)

if uploaded_file is not None:
    st.success(f"已成功上傳：{uploaded_file.name}")

    st.subheader("教材分析")

    st.info("目前為 Prototype：以下分析結果暫時使用測試資料。")

    st.write("偵測到 **18 個核心概念**")

    st.markdown("""
**主要內容**

- Gram-positive / Gram-negative bacteria
- Gram staining
- Acid-fast staining
- Antimicrobial mechanisms
- Antibiotic resistance
""")

    st.write("建議測驗題數：**18 題**")

    st.button("開始測驗")
