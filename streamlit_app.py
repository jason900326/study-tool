import streamlit as st


# =========================================================
# 網頁基本設定
# =========================================================

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

# 儲存使用者答案
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
# 儲存答案
# =========================================================

def save_answer(question_index):

    widget_key = f"radio_{question_index}"

    if widget_key in st.session_state:
        st.session_state.answers[question_index] = (
            st.session_state[widget_key]
        )


def save_uncertain(question_index):

    widget_key = f"uncertain_{question_index}"

    if widget_key in st.session_state:
        st.session_state.uncertain_answers[question_index] = (
            st.session_state[widget_key]
        )


# =========================================================
# 結束測驗 Dialog
# =========================================================

@st.dialog("結束測驗")
def finish_quiz_dialog():

    unanswered = []

    for i in range(len(questions)):

        answer = st.session_state.answers.get(i)
        uncertain = st.session_state.uncertain_answers.get(i, False)

        # 沒選答案也沒按 ❓ 才算未作答
        if answer is None and not uncertain:
            unanswered.append(i + 1)

    # -----------------------------------------------------
    # 有未作答題目
    # -----------------------------------------------------

    if unanswered:

        question_list = "、".join(
            [f"第 {number} 題" for number in unanswered]
        )

        st.warning(
            f"你還有未作答的題目：{question_list}"
        )

        st.write(
            "你可以返回測驗繼續作答，"
            "或直接結束測驗。"
        )

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

    # -----------------------------------------------------
    # 所有題目皆已完成
    # -----------------------------------------------------

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

def show_home():

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

        st.markdown(
            """
**主要內容**

- Gram-positive / Gram-negative bacteria
- Gram staining
- Acid-fast staining
- Antimicrobial mechanisms
- Antibiotic resistance
"""
        )

        st.write("建議測驗題數：**18 題**")

        if st.button(
            "開始測驗",
            use_container_width=True
        ):

            st.session_state.page = "quiz"
            st.session_state.question_index = 0

            # 開始新測驗時清空舊資料
            st.session_state.answers = {}
            st.session_state.uncertain_answers = {}

            # 清掉舊 widget state
            for i in range(len(questions)):

                radio_key = f"radio_{i}"
                uncertain_key = f"uncertain_{i}"

                if radio_key in st.session_state:
                    del st.session_state[radio_key]

                if uncertain_key in st.session_state:
                    del st.session_state[uncertain_key]

            st.rerun()


# =========================================================
# 測驗頁
# =========================================================

def show_quiz():

    current = st.session_state.question_index
    question = questions[current]

    # =====================================================
    # 上方：題號 + 右上角結束測驗
    # =====================================================

    top_left, top_right = st.columns([7, 1.4])

    with top_left:

        st.markdown(
            f"""
            <div style="
                padding-top: 8px;
                font-size: 18px;
                font-weight: 600;
            ">
                Question {current + 1} / {len(questions)}
            </div>
            """,
            unsafe_allow_html=True
        )

    with top_right:

        if st.button(
            "結束測驗",
            use_container_width=True,
            key=f"finish_top_{current}"
        ):
            finish_quiz_dialog()

    # =====================================================
    # 進度條
    # =====================================================

    st.progress(
        (current + 1) / len(questions)
    )

    st.divider()

    # =====================================================
    # 題目
    # =====================================================

    st.subheader(question["question"])

    # -----------------------------------------------------
    # 如果之前已經答過，把答案帶回畫面
    # -----------------------------------------------------

    radio_key = f"radio_{current}"

    if radio_key not in st.session_state:

        saved_answer = st.session_state.answers.get(current)

        if saved_answer is not None:
            st.session_state[radio_key] = saved_answer

    # -----------------------------------------------------
    # 選項
    # -----------------------------------------------------

    st.radio(
        "請選擇答案",
        question["options"],
        index=None,
        key=radio_key,
        on_change=save_answer,
        args=(current,)
    )

    # =====================================================
    # ❓ 不確定
    # =====================================================

    uncertain_key = f"uncertain_{current}"

    if uncertain_key not in st.session_state:

        saved_uncertain = (
            st.session_state.uncertain_answers.get(
                current,
                False
            )
        )

        st.session_state[uncertain_key] = saved_uncertain

    st.checkbox(
        "❓ 我不確定",
        key=uncertain_key,
        on_change=save_uncertain,
        args=(current,)
    )

    # =====================================================
    # 顯示目前狀態
    # =====================================================

    answer_exists = (
        current in st.session_state.answers
    )

    uncertain = (
        st.session_state.uncertain_answers.get(
            current,
            False
        )
    )

    if answer_exists and uncertain:

        st.caption(
            "已作答 · ❓ 不確定"
        )

    elif answer_exists:

        st.caption(
            "已作答"
        )

    elif uncertain:

        st.caption(
            "❓ 已標記為不確定"
        )

    # =====================================================
    # 下方 Navigation
    # =====================================================

    st.divider()

    total_questions = len(questions)

    # -----------------------------------------------------
    # Q1：只有下一題
    # -----------------------------------------------------

    if current == 0:

        empty_col, next_col = st.columns(2)

        with next_col:

            if st.button(
                "下一題 →",
                use_container_width=True,
                key=f"next_{current}"
            ):

                st.session_state.question_index += 1
                st.rerun()

    # -----------------------------------------------------
    # 最後一題：只有上一題
    # -----------------------------------------------------

    elif current == total_questions - 1:

        prev_col, empty_col = st.columns(2)

        with prev_col:

            if st.button(
                "← 上一題",
                use_container_width=True,
                key=f"prev_{current}"
            ):

                st.session_state.question_index -= 1
                st.rerun()

    # -----------------------------------------------------
    # 中間題目：上一題 + 下一題
    # -----------------------------------------------------

    else:

        prev_col, next_col = st.columns(2)

        with prev_col:

            if st.button(
                "← 上一題",
                use_container_width=True,
                key=f"prev_{current}"
            ):

                st.session_state.question_index -= 1
                st.rerun()

        with next_col:

            if st.button(
                "下一題 →",
                use_container_width=True,
                key=f"next_{current}"
            ):

                st.session_state.question_index += 1
                st.rerun()


# =========================================================
# 結果頁
# =========================================================

def show_result():

    st.title("測驗完成")

    # =====================================================
    # 計算分數
    # =====================================================

    correct_count = 0

    for i, question in enumerate(questions):

        user_answer = (
            st.session_state.answers.get(i)
        )

        correct_answer = (
            question["options"][question["answer"]]
        )

        if user_answer == correct_answer:
            correct_count += 1

    total_questions = len(questions)

    percentage = round(
        correct_count / total_questions * 100
    )

    # =====================================================
    # 顯示分數
    # =====================================================

    st.subheader(
        f"{correct_count} / {total_questions}（{percentage}%）"
    )

    st.divider()

    # =====================================================
    # 答題結果
    # =====================================================

    st.subheader("答題結果")

    for i, question in enumerate(questions):

        user_answer = (
            st.session_state.answers.get(i)
        )

        uncertain = (
            st.session_state.uncertain_answers.get(
                i,
                False
            )
        )

        correct_answer = (
            question["options"][question["answer"]]
        )

        is_correct = (
            user_answer == correct_answer
        )

        # -------------------------------------------------
        # 答對
        # -------------------------------------------------

        if is_correct and not uncertain:

            st.write(
                f"**第 {i + 1} 題**　✅"
            )

        # -------------------------------------------------
        # 答對 + ❓
        # -------------------------------------------------

        elif is_correct and uncertain:

            st.write(
                f"**第 {i + 1} 題**　✅ ❓"
            )

        # -------------------------------------------------
        # 答錯
        # -------------------------------------------------

        elif user_answer is not None:

            st.write(
                f"**第 {i + 1} 題**　❌"
            )

        # -------------------------------------------------
        # 沒有答案，但按了 ❓
        # -------------------------------------------------

        elif uncertain:

            st.write(
                f"**第 {i + 1} 題**　❓"
            )

        # -------------------------------------------------
        # 完全未作答
        # -------------------------------------------------

        else:

            st.write(
                f"**第 {i + 1} 題**　未作答"
            )

    st.divider()

    # =====================================================
    # 回首頁
    # =====================================================

    if st.button(
        "回首頁",
        use_container_width=True
    ):

        st.session_state.page = "home"
        st.session_state.question_index = 0

        st.rerun()


# =========================================================
# Page Router
# =========================================================

if st.session_state.page == "home":

    show_home()

elif st.session_state.page == "quiz":

    show_quiz()

elif st.session_state.page == "result":

    show_result()
