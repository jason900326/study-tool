import streamlit as st

st.set_page_config(
    page_title="Study Tool",
    page_icon="📚",
    layout="wide"
)

# =========================================================
# Session State
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "home"

if "question_index" not in st.session_state:
    st.session_state.question_index = 0

# 真正儲存使用者答案的地方
if "answers" not in st.session_state:
    st.session_state.answers = {}

# 儲存 ❓ 狀態
if "uncertain_answers" not in st.session_state:
    st.session_state.uncertain_answers = {}


# =========================================================
# 假題目資料
# =========================================================

questions = [
    {
        "question": "下列何者是 Gram-negative bacteria 的特徵？",
        "options": [
            "具有厚的 peptidoglycan layer",
            "具有 outer membrane",
            "沒有 LPS",
            "沒有 periplasm"
        ],
        "answer": 1
    },
    {
        "question": "Gram stain 中的主要脫色步驟使用何者？",
        "options": [
            "Crystal violet",
            "Iodine",
            "Alcohol / acetone",
            "Safranin"
        ],
        "answer": 2
    },
    {
        "question": "Vancomycin 主要作用在哪個細菌結構？",
        "options": [
            "DNA",
            "Cell wall",
            "30S ribosome",
            "Cytoplasmic membrane"
        ],
        "answer": 1
    }
]


# =========================================================
# 儲存答案的 function
# =========================================================

def save_answer(question_index):
    widget_key = f"radio_{question_index}"

    if widget_key in st.session_state:
        st.session_state.answers[question_index] = st.session_state[widget_key]


def save_uncertain(question_index):
    widget_key = f"uncertain_{question_index}"

    if widget_key in st.session_state:
        st.session_state.uncertain_answers[question_index] = (
            st.session_state[widget_key]
        )


# =========================================================
# 結束測驗確認視窗
# =========================================================

@st.dialog("結束測驗")
def finish_quiz_dialog():

    unanswered = []

    for i in range(len(questions)):

        answer = st.session_state.answers.get(i)
        uncertain = st.session_state.uncertain_answers.get(i, False)

        # 沒答案，而且也沒有按 ❓，才算真正漏答
        if answer is None and not uncertain:
            unanswered.append(i + 1)

    if unanswered:

        question_list = "、".join(
            [f"第 {number} 題" for number in unanswered]
        )

        st.warning(
            f"你還有未作答的題目：{question_list}"
        )

        st.write("你可以返回測驗繼續作答，或仍然結束測驗。")

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "返回測驗",
                use_container_width=True
            ):
                st.rerun()

        with col2:
            if st.button(
                "仍然結束",
                use_container_width=True
            ):
                st.session_state.page = "result"
                st.rerun()

    else:

        st.success("所有題目皆已完成。")

        if st.button(
            "查看結果",
            use_container_width=True
        ):
            st.session_state.page = "result"
            st.rerun()


# =========================================================
# 首頁
# =========================================================

if st.session_state.page == "home":

    st.title("📚 把教材變成你的測驗")

    st.write(
        "上傳你的課堂講義，系統會整理教材內容，"
        "並根據重要概念產生測驗。"
    )

    st.divider()

    uploaded_file = st.file_uploader(
        "上傳 PDF",
        type=["pdf"]
    )

    if uploaded_file is not None:

        st.success(
            f"已成功上傳：{uploaded_file.name}"
        )

        st.subheader("教材分析")

        st.info(
            "目前為 Prototype：以下分析結果暫時使用測試資料。"
        )

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

        if st.button("開始測驗"):

            st.session_state.page = "quiz"
            st.session_state.question_index = 0

            # 每次開始新測驗時清除舊資料
            st.session_state.answers = {}
            st.session_state.uncertain_answers = {}

            st.rerun()


# =========================================================
# 測驗頁
# =========================================================

elif st.session_state.page == "quiz":

    current = st.session_state.question_index
    question = questions[current]

    # -----------------------------------------------------
    # 上一題 / 題號 / 下一題
    # -----------------------------------------------------

    left, center, right = st.columns([1, 6, 1])

    with left:

        if current > 0:

            if st.button(
                "← 上一題",
                use_container_width=True
            ):
                st.session_state.question_index -= 1
                st.rerun()

    with center:

        st.markdown(
            f"""
            <div style="
                text-align: center;
                padding-top: 8px;
            ">
                Question {current + 1} / {len(questions)}
            </div>
            """,
            unsafe_allow_html=True
        )

    with right:

        if current < len(questions) - 1:

            if st.button(
                "下一題 →",
                use_container_width=True
            ):
                st.session_state.question_index += 1
                st.rerun()

    st.progress(
        (current + 1) / len(questions)
    )

    st.divider()

    # -----------------------------------------------------
    # 題目
    # -----------------------------------------------------

    st.subheader(question["question"])

    saved_answer = st.session_state.answers.get(current)

    if saved_answer in question["options"]:
        saved_index = question["options"].index(saved_answer)
    else:
        saved_index = None

    st.radio(
        "請選擇答案",
        question["options"],
        index=saved_index,
        key=f"radio_{current}",
        on_change=save_answer,
        args=(current,)
    )

    saved_uncertain = (
        st.session_state.uncertain_answers.get(current, False)
    )

    st.checkbox(
        "❓ 我不確定",
        value=saved_uncertain,
        key=f"uncertain_{current}",
        on_change=save_uncertain,
        args=(current,)
    )

    # -----------------------------------------------------
    # 顯示目前狀態
    # -----------------------------------------------------

    answer_exists = (
        current in st.session_state.answers
    )

    uncertain = (
        st.session_state.uncertain_answers.get(current, False)
    )

    if answer_exists and uncertain:
        st.caption("已作答 · ❓ 不確定")

    elif answer_exists:
        st.caption("已作答")

    elif uncertain:
        st.caption("❓ 已標記為不確定")

    st.divider()

    # -----------------------------------------------------
    # 結束測驗
    # -----------------------------------------------------

    if st.button("結束測驗"):
        finish_quiz_dialog()


# =========================================================
# 結果頁（暫時）
# =========================================================

elif st.session_state.page == "result":

    st.title("測驗完成")

    st.info(
        "下一個 Prototype 階段會在這裡加入真正的判分與錯題檢討。"
    )

    st.subheader("目前記錄")

    for i, question in enumerate(questions):

        answer = st.session_state.answers.get(i, "未選擇")
        uncertain = st.session_state.uncertain_answers.get(i, False)

        status = "❓" if uncertain else ""

        st.write(
            f"**第 {i + 1} 題：** {answer} {status}"
        )

    st.divider()

    if st.button("回首頁"):

        st.session_state.page = "home"
        st.session_state.question_index = 0

        st.rerun()
