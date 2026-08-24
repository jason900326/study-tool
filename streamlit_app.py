import streamlit as st
import html
from supabase import create_client
from pypdf import PdfReader


# =========================================================
# 網頁基本設定
# =========================================================

st.set_page_config(
    page_title="Study Tool",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================================================
# Supabase
# =========================================================

@st.cache_resource
def get_supabase():

    url = str(
        st.secrets["SUPABASE_URL"]
    ).strip()

    key = str(
        st.secrets["SUPABASE_KEY"]
    ).strip()

    url = (
        url
        .replace("\ufeff", "")
        .replace("\u200b", "")
    )

    key = (
        key
        .replace("\ufeff", "")
        .replace("\u200b", "")
    )

    return create_client(
        url,
        key
    )


def test_database_connection():

    try:

        supabase = get_supabase()

        (
            supabase
            .table("mistakes")
            .select("id")
            .limit(1)
            .execute()
        )

        return True, None

    except Exception as error:

        return (
            False,
            f"{type(error).__name__}: {str(error)}"
        )


# =========================================================
# Session State
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "home"

if "question_index" not in st.session_state:
    st.session_state.question_index = 0

if "answers" not in st.session_state:
    st.session_state.answers = {}

if "uncertain_answers" not in st.session_state:
    st.session_state.uncertain_answers = {}

if "error_labels" not in st.session_state:
    st.session_state.error_labels = {}

if "mistakes_saved" not in st.session_state:
    st.session_state.mistakes_saved = False

if "mistake_record_ids" not in st.session_state:
    st.session_state.mistake_record_ids = {}

if "label_sync_error" not in st.session_state:
    st.session_state.label_sync_error = None


# =========================================================
# Prototype 題目資料
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
        "answer": 1,
        "subject": "臨床微生物學",
        "concept": "Gram-positive / Gram-negative cell envelope",
        "review_type": "table",
        "review_points": [
            "Gram-negative bacteria 具有 outer membrane。",
            "Gram-negative bacteria 的 peptidoglycan layer 較薄。",
            "LPS 位於 Gram-negative bacteria 的 outer membrane。"
        ],
        "comparison": {
            "特徵": [
                "Peptidoglycan",
                "Outer membrane",
                "LPS"
            ],
            "Gram-positive": [
                "厚",
                "無",
                "無"
            ],
            "Gram-negative": [
                "薄",
                "有",
                "有"
            ]
        },
        "source": "Prototype PDF · Page 8"
    },

    {
        "question": "Gram stain 中的主要脫色步驟使用何者？",
        "options": [
            "Crystal violet",
            "Iodine",
            "Alcohol / acetone",
            "Safranin"
        ],
        "answer": 2,
        "subject": "臨床微生物學",
        "concept": "Gram staining procedure",
        "review_type": "bullets",
        "review_points": [
            "Crystal violet 是 primary stain。",
            "Iodine 是 mordant。",
            "Alcohol / acetone 是 decolorizer。",
            "Safranin 是 counterstain。"
        ],
        "source": "Prototype PDF · Page 9"
    },

    {
        "question": "Vancomycin 主要作用在哪個細菌結構？",
        "options": [
            "DNA",
            "Cell wall",
            "30S ribosome",
            "Cytoplasmic membrane"
        ],
        "answer": 1,
        "subject": "臨床微生物學",
        "concept": "Vancomycin mechanism of action",
        "review_type": "bullets",
        "review_points": [
            "Vancomycin 屬於 glycopeptide。",
            "作用位置與 bacterial cell wall synthesis 有關。",
            "其作用與 peptidoglycan precursor 的 D-Ala-D-Ala 有關。"
        ],
        "source": "Prototype PDF · Page 30"
    }
]


# =========================================================
# PDF 解析
# =========================================================

def extract_pdf_text(uploaded_file):

    reader = PdfReader(uploaded_file)

    page_count = len(reader.pages)

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        try:

            text = page.extract_text()

            if text is None:
                text = ""

        except Exception:

            text = ""

        pages.append(
            {
                "page": page_number,
                "text": text.strip()
            }
        )

    return page_count, pages


def create_pdf_preview(
    pages,
    max_pages=3,
    max_chars_per_page=1500
):

    preview_parts = []

    for page_data in pages[:max_pages]:

        page_number = (
            page_data["page"]
        )

        text = (
            page_data["text"]
        )

        if not text:

            text = "（此頁未擷取到可讀取文字）"

        if (
            len(text)
            > max_chars_per_page
        ):

            text = (
                text[:max_chars_per_page]
                + "..."
            )

        preview_parts.append(
            f"--- 第 {page_number} 頁 ---\n{text}"
        )

    return "\n\n".join(
        preview_parts
    )


# =========================================================
# Sidebar
# =========================================================

def show_sidebar():

    with st.sidebar:

        st.title(
            "📚 Study Tool"
        )

        if st.button(
            "首頁",
            use_container_width=True
        ):

            st.session_state.page = "home"
            st.rerun()

        if st.button(
            "錯題庫",
            use_container_width=True
        ):

            st.session_state.page = "mistakes"
            st.rerun()

        st.button(
            "弱點分析",
            use_container_width=True,
            disabled=True
        )

        st.divider()

        connected, error = (
            test_database_connection()
        )

        if connected:

            st.success(
                "Database connected"
            )

        else:

            st.error(
                "Database connection failed"
            )

            with st.expander(
                "查看錯誤"
            ):

                st.code(error)

        st.caption(
            "Prototype v0.1"
        )


# =========================================================
# 彩色答案選項
# =========================================================

def render_answer_options(
    options,
    correct_answer,
    user_answer
):

    option_labels = [
        "A",
        "B",
        "C",
        "D"
    ]

    for (
        option_label,
        option_text
    ) in zip(
        option_labels,
        options
    ):

        is_correct = (
            option_text
            == correct_answer
        )

        is_user_answer = (
            option_text
            == user_answer
        )

        background = (
            "rgba(128, 128, 128, 0.08)"
        )

        border = (
            "1px solid "
            "rgba(128, 128, 128, 0.25)"
        )

        if is_correct:

            background = (
                "rgba(46, 204, 113, 0.18)"
            )

            border = (
                "1px solid "
                "rgba(46, 204, 113, 0.55)"
            )

        if (
            is_user_answer
            and not is_correct
        ):

            background = (
                "rgba(231, 76, 60, 0.18)"
            )

            border = (
                "1px solid "
                "rgba(231, 76, 60, 0.55)"
            )

        if (
            is_user_answer
            and is_correct
        ):

            background = (
                "rgba(46, 204, 113, 0.18)"
            )

            border = (
                "2px solid "
                "rgba(231, 76, 60, 0.70)"
            )

        safe_option = (
            html.escape(
                str(option_text)
            )
        )

        st.markdown(
            f"""
            <div style="
                background: {background};
                border: {border};
                border-radius: 10px;
                padding: 12px 16px;
                margin-bottom: 9px;
            ">
                <strong>{option_label}.</strong>
                {safe_option}
            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# 儲存答案
# =========================================================

def save_answer(
    question_index
):

    widget_key = (
        f"radio_{question_index}"
    )

    if (
        widget_key
        in st.session_state
    ):

        st.session_state.answers[
            question_index
        ] = (
            st.session_state[
                widget_key
            ]
        )


def save_uncertain(
    question_index
):

    widget_key = (
        f"uncertain_{question_index}"
    )

    if (
        widget_key
        in st.session_state
    ):

        value = (
            st.session_state[
                widget_key
            ]
        )

        st.session_state.uncertain_answers[
            question_index
        ] = value

        if value:

            if (
                question_index
                not in
                st.session_state.error_labels
            ):

                st.session_state.error_labels[
                    question_index
                ] = "觀念不熟"


# =========================================================
# Label 同步 Supabase
# =========================================================

def save_error_label(
    question_index
):

    widget_key = (
        f"error_label_{question_index}"
    )

    if (
        widget_key
        not in st.session_state
    ):
        return

    new_label = (
        st.session_state[
            widget_key
        ]
    )

    st.session_state.error_labels[
        question_index
    ] = new_label

    record_id = (
        st.session_state
        .mistake_record_ids
        .get(question_index)
    )

    if record_id is None:

        st.session_state.label_sync_error = (
            f"找不到第 {question_index + 1} 題"
            "對應的資料庫紀錄。"
        )

        return

    try:

        supabase = get_supabase()

        (
            supabase
            .table("mistakes")
            .update(
                {
                    "label": new_label
                }
            )
            .eq(
                "id",
                record_id
            )
            .execute()
        )

        st.session_state.label_sync_error = None

    except Exception as error:

        st.session_state.label_sync_error = (
            f"{type(error).__name__}: "
            f"{str(error)}"
        )


# =========================================================
# 錯題 INSERT
# =========================================================

def save_mistakes_to_database():

    if st.session_state.mistakes_saved:
        return

    supabase = get_supabase()

    st.session_state.mistake_record_ids = {}

    for i, question in enumerate(
        questions
    ):

        user_answer = (
            st.session_state
            .answers
            .get(i)
        )

        uncertain = (
            st.session_state
            .uncertain_answers
            .get(
                i,
                False
            )
        )

        correct_answer = (
            question["options"][
                question["answer"]
            ]
        )

        is_correct = (
            user_answer
            == correct_answer
        )

        needs_review = (
            (not is_correct)
            or uncertain
        )

        if not needs_review:
            continue

        row = {
            "subject":
                question["subject"],

            "concept":
                question["concept"],

            "question":
                question["question"],

            "options":
                question["options"],

            "user_answer":
                user_answer,

            "correct_answer":
                correct_answer,

            "uncertain":
                uncertain,

            "is_correct":
                is_correct,

            "label":
                st.session_state
                .error_labels
                .get(i),

            "source":
                question["source"]
        }

        response = (
            supabase
            .table("mistakes")
            .insert(row)
            .execute()
        )

        if (
            response.data
            and len(response.data) > 0
        ):

            database_id = (
                response.data[0]["id"]
            )

            st.session_state.mistake_record_ids[
                i
            ] = database_id

    st.session_state.mistakes_saved = True


# =========================================================
# 讀取錯題
# =========================================================

def load_mistakes_from_database():

    supabase = get_supabase()

    response = (
        supabase
        .table("mistakes")
        .select("*")
        .order(
            "created_at",
            desc=True
        )
        .execute()
    )

    return response.data


# =========================================================
# 結束測驗 Dialog
# =========================================================

@st.dialog(
    "結束測驗"
)
def finish_quiz_dialog():

    unanswered = []

    for i in range(
        len(questions)
    ):

        answer = (
            st.session_state
            .answers
            .get(i)
        )

        uncertain = (
            st.session_state
            .uncertain_answers
            .get(
                i,
                False
            )
        )

        if (
            answer is None
            and not uncertain
        ):

            unanswered.append(
                i + 1
            )

    if unanswered:

        question_list = (
            "、".join(
                [
                    f"第 {number} 題"
                    for number
                    in unanswered
                ]
            )
        )

        st.warning(
            f"你還有未作答的題目："
            f"{question_list}"
        )

        st.write(
            "你可以返回測驗繼續作答，"
            "或直接結束測驗。"
        )

        col1, col2 = (
            st.columns(2)
        )

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

                try:

                    save_mistakes_to_database()

                except Exception as error:

                    st.error(
                        "錯題儲存失敗"
                    )

                    st.code(
                        str(error)
                    )

                    return

                st.session_state.page = (
                    "result"
                )

                st.rerun()

    else:

        st.success(
            "所有題目皆已完成。"
        )

        if st.button(
            "查看結果",
            use_container_width=True
        ):

            try:

                save_mistakes_to_database()

            except Exception as error:

                st.error(
                    "錯題儲存失敗"
                )

                st.code(
                    str(error)
                )

                return

            st.session_state.page = (
                "result"
            )

            st.rerun()


# =========================================================
# 首頁
# =========================================================

def show_home():

    st.title(
        "📚 把教材變成你的測驗"
    )

    st.write(
        "上傳你的課堂講義，"
        "系統會讀取 PDF 內容，"
        "後續再根據教材產生測驗。"
    )

    st.divider()

    uploaded_file = (
        st.file_uploader(
            "上傳 PDF",
            type=["pdf"]
        )
    )

    if (
        uploaded_file
        is not None
    ):

        st.success(
            f"已成功上傳："
            f"{uploaded_file.name}"
        )

        st.subheader(
            "PDF 解析結果"
        )

        try:

            page_count, pages = (
                extract_pdf_text(
                    uploaded_file
                )
            )

        except Exception as error:

            st.error(
                "PDF 讀取失敗"
            )

            st.code(
                f"{type(error).__name__}: "
                f"{str(error)}"
            )

            return

        # ================================================
        # 基本資訊
        # ================================================

        total_chars = sum(
            len(
                page["text"]
            )
            for page in pages
        )

        pages_with_text = sum(
            1
            for page in pages
            if page["text"]
        )

        col1, col2, col3 = (
            st.columns(3)
        )

        col1.metric(
            "PDF 頁數",
            page_count
        )

        col2.metric(
            "可讀文字頁",
            f"{pages_with_text} / {page_count}"
        )

        col3.metric(
            "擷取字元數",
            f"{total_chars:,}"
        )

        st.divider()

        # ================================================
        # 文字預覽
        # ================================================

        st.subheader(
            "文字預覽"
        )

        st.caption(
            "目前只顯示前 3 頁，"
            "用來確認 PDF 是否能正常讀取。"
        )

        preview = (
            create_pdf_preview(
                pages,
                max_pages=3
            )
        )

        st.text_area(
            "PDF 文字內容",
            value=preview,
            height=420,
            disabled=True,
            label_visibility="collapsed"
        )

        # ================================================
        # 無文字 PDF 提醒
        # ================================================

        if pages_with_text == 0:

            st.warning(
                "這份 PDF 沒有擷取到可讀取文字。"
                "它可能是掃描圖片型 PDF，"
                "之後需要另外處理 OCR。"
            )

        elif (
            pages_with_text
            < page_count
        ):

            st.warning(
                "部分頁面沒有擷取到文字。"
                "可能包含圖片、掃描頁面或特殊排版。"
            )

        else:

            st.success(
                "PDF 文字擷取正常。"
            )

        st.divider()

        st.info(
            "目前測驗仍使用 Prototype 假題目。"
            "下一步才會把實際 PDF 內容送進 AI 分析。"
        )

        if st.button(
            "開始 Prototype 測驗",
            use_container_width=True
        ):

            st.session_state.page = (
                "quiz"
            )

            st.session_state.question_index = 0

            st.session_state.answers = {}

            st.session_state.uncertain_answers = {}

            st.session_state.error_labels = {}

            st.session_state.mistakes_saved = False

            st.session_state.mistake_record_ids = {}

            st.session_state.label_sync_error = None

            for i in range(
                len(questions)
            ):

                radio_key = (
                    f"radio_{i}"
                )

                uncertain_key = (
                    f"uncertain_{i}"
                )

                label_key = (
                    f"error_label_{i}"
                )

                if (
                    radio_key
                    in st.session_state
                ):

                    del st.session_state[
                        radio_key
                    ]

                if (
                    uncertain_key
                    in st.session_state
                ):

                    del st.session_state[
                        uncertain_key
                    ]

                if (
                    label_key
                    in st.session_state
                ):

                    del st.session_state[
                        label_key
                    ]

            st.rerun()


# =========================================================
# 測驗頁
# =========================================================

def show_quiz():

    current = (
        st.session_state
        .question_index
    )

    question = (
        questions[current]
    )

    top_left, top_right = (
        st.columns(
            [7, 1.4]
        )
    )

    with top_left:

        st.markdown(
            f"""
            <div style="
                padding-top: 8px;
                font-size: 18px;
                font-weight: 600;
            ">
                Question {current + 1}
                /
                {len(questions)}
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

    st.progress(
        (current + 1)
        / len(questions)
    )

    st.divider()

    st.subheader(
        question["question"]
    )

    radio_key = (
        f"radio_{current}"
    )

    if (
        radio_key
        not in st.session_state
    ):

        saved_answer = (
            st.session_state
            .answers
            .get(current)
        )

        if (
            saved_answer
            is not None
        ):

            st.session_state[
                radio_key
            ] = saved_answer

    st.radio(
        "請選擇答案",
        question["options"],
        index=None,
        key=radio_key,
        on_change=save_answer,
        args=(current,)
    )

    uncertain_key = (
        f"uncertain_{current}"
    )

    if (
        uncertain_key
        not in st.session_state
    ):

        saved_uncertain = (
            st.session_state
            .uncertain_answers
            .get(
                current,
                False
            )
        )

        st.session_state[
            uncertain_key
        ] = saved_uncertain

    st.checkbox(
        "❓ 我不確定",
        key=uncertain_key,
        on_change=save_uncertain,
        args=(current,)
    )

    answer_exists = (
        current
        in st.session_state.answers
    )

    uncertain = (
        st.session_state
        .uncertain_answers
        .get(
            current,
            False
        )
    )

    if (
        answer_exists
        and uncertain
    ):

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

    st.divider()

    total_questions = (
        len(questions)
    )

    if current == 0:

        empty_col, next_col = (
            st.columns(2)
        )

        with next_col:

            if st.button(
                "下一題 →",
                use_container_width=True,
                key=f"next_{current}"
            ):

                st.session_state.question_index += 1
                st.rerun()

    elif (
        current
        == total_questions - 1
    ):

        prev_col, empty_col = (
            st.columns(2)
        )

        with prev_col:

            if st.button(
                "← 上一題",
                use_container_width=True,
                key=f"prev_{current}"
            ):

                st.session_state.question_index -= 1
                st.rerun()

    else:

        prev_col, next_col = (
            st.columns(2)
        )

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
# 錯題檢討
# =========================================================

def show_review_item(
    question_index
):

    question = (
        questions[
            question_index
        ]
    )

    user_answer = (
        st.session_state
        .answers
        .get(
            question_index
        )
    )

    uncertain = (
        st.session_state
        .uncertain_answers
        .get(
            question_index,
            False
        )
    )

    correct_answer = (
        question["options"][
            question["answer"]
        ]
    )

    is_correct = (
        user_answer
        == correct_answer
    )

    if (
        is_correct
        and uncertain
    ):

        title = (
            f"第 {question_index + 1} 題　✅ ❓"
        )

    elif (
        user_answer is None
        and uncertain
    ):

        title = (
            f"第 {question_index + 1} 題　❓"
        )

    else:

        title = (
            f"第 {question_index + 1} 題　❌"
        )

    with st.expander(
        title,
        expanded=False
    ):

        st.markdown(
            f"### {question['question']}"
        )

        render_answer_options(
            question["options"],
            correct_answer,
            user_answer
        )

        if (
            user_answer
            is None
        ):

            st.caption(
                "你沒有選擇答案，"
                "但曾標記 ❓。"
            )

        st.divider()

        st.markdown(
            "### 核心觀念"
        )

        st.write(
            question["concept"]
        )

        if (
            question[
                "review_type"
            ]
            == "table"
        ):

            comparison = (
                question[
                    "comparison"
                ]
            )

            rows = []

            for i in range(
                len(
                    comparison[
                        "特徵"
                    ]
                )
            ):

                rows.append(
                    {
                        "特徵":
                            comparison[
                                "特徵"
                            ][i],

                        "Gram-positive":
                            comparison[
                                "Gram-positive"
                            ][i],

                        "Gram-negative":
                            comparison[
                                "Gram-negative"
                            ][i]
                    }
                )

            st.table(rows)

        else:

            for point in (
                question[
                    "review_points"
                ]
            ):

                st.markdown(
                    f"- {point}"
                )

        st.markdown(
            "### 📖 教材根據"
        )

        st.caption(
            question["source"]
        )

        st.divider()

        st.markdown(
            "**你認為這次需要檢討的原因是？**"
        )

        label_options = [
            "粗心大意",
            "觀念不熟",
            "完全沒看過"
        ]

        saved_label = (
            st.session_state
            .error_labels
            .get(
                question_index
            )
        )

        if (
            saved_label
            in label_options
        ):

            label_index = (
                label_options.index(
                    saved_label
                )
            )

        else:

            label_index = None

        label_key = (
            f"error_label_{question_index}"
        )

        st.radio(
            "錯誤分類",
            label_options,
            index=label_index,
            horizontal=True,
            key=label_key,
            on_change=save_error_label,
            args=(
                question_index,
            ),
            label_visibility="collapsed"
        )

        selected_label = (
            st.session_state
            .error_labels
            .get(
                question_index
            )
        )

        if selected_label:

            st.caption(
                f"已標記：{selected_label}"
            )


# =========================================================
# 結果頁
# =========================================================

def show_result():

    st.title(
        "測驗完成"
    )

    correct_count = 0

    for i, question in enumerate(
        questions
    ):

        user_answer = (
            st.session_state
            .answers
            .get(i)
        )

        correct_answer = (
            question["options"][
                question["answer"]
            ]
        )

        if (
            user_answer
            == correct_answer
        ):

            correct_count += 1

    total_questions = (
        len(questions)
    )

    percentage = round(
        correct_count
        / total_questions
        * 100
    )

    st.subheader(
        f"{correct_count} / "
        f"{total_questions}"
        f"（{percentage}%）"
    )

    st.divider()

    st.subheader(
        "答題結果"
    )

    review_questions = []

    for i, question in enumerate(
        questions
    ):

        user_answer = (
            st.session_state
            .answers
            .get(i)
        )

        uncertain = (
            st.session_state
            .uncertain_answers
            .get(
                i,
                False
            )
        )

        correct_answer = (
            question["options"][
                question["answer"]
            ]
        )

        is_correct = (
            user_answer
            == correct_answer
        )

        if (
            is_correct
            and not uncertain
        ):

            st.write(
                f"**第 {i + 1} 題**　✅"
            )

        elif (
            is_correct
            and uncertain
        ):

            st.write(
                f"**第 {i + 1} 題**　✅ ❓"
            )

            review_questions.append(i)

        elif (
            user_answer
            is not None
        ):

            st.write(
                f"**第 {i + 1} 題**　❌"
            )

            review_questions.append(i)

        elif uncertain:

            st.write(
                f"**第 {i + 1} 題**　❓"
            )

            review_questions.append(i)

        else:

            st.write(
                f"**第 {i + 1} 題**　未作答"
            )

    if review_questions:

        st.divider()

        st.subheader(
            "需要檢討"
        )

        st.caption(
            "答錯或曾標記 ❓ 的題目"
            "會出現在這裡。"
        )

        for question_index in (
            review_questions
        ):

            show_review_item(
                question_index
            )

        if (
            st.session_state
            .label_sync_error
        ):

            st.warning(
                "部分錯題分類尚未同步到資料庫。"
            )

            st.code(
                st.session_state
                .label_sync_error
            )

    else:

        st.success(
            "這次沒有需要檢討的題目。"
        )

    st.divider()

    nav1, nav2 = (
        st.columns(2)
    )

    with nav1:

        if st.button(
            "查看錯題庫",
            use_container_width=True
        ):

            st.session_state.page = (
                "mistakes"
            )

            st.rerun()

    with nav2:

        if st.button(
            "回首頁",
            use_container_width=True
        ):

            st.session_state.page = (
                "home"
            )

            st.session_state.question_index = 0

            st.rerun()


# =========================================================
# 錯題庫
# =========================================================

def show_mistake_bank():

    st.title(
        "📘 錯題庫"
    )

    try:

        mistake_bank = (
            load_mistakes_from_database()
        )

    except Exception as error:

        st.error(
            "無法讀取錯題庫"
        )

        st.code(
            str(error)
        )

        return

    if not mistake_bank:

        st.info(
            "目前還沒有錯題紀錄。"
        )

        return

    total = len(
        mistake_bank
    )

    careless = 0
    unfamiliar = 0
    unseen = 0

    for item in mistake_bank:

        label = (
            item.get(
                "label"
            )
        )

        if (
            label
            == "粗心大意"
        ):

            careless += 1

        elif (
            label
            == "觀念不熟"
        ):

            unfamiliar += 1

        elif (
            label
            == "完全沒看過"
        ):

            unseen += 1

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    col1.metric(
        "需複習",
        total
    )

    col2.metric(
        "粗心大意",
        careless
    )

    col3.metric(
        "觀念不熟",
        unfamiliar
    )

    col4.metric(
        "完全沒看過",
        unseen
    )

    st.divider()

    subjects = {}

    for item in mistake_bank:

        subject = (
            item.get(
                "subject",
                "未分類"
            )
        )

        if (
            subject
            not in subjects
        ):

            subjects[
                subject
            ] = []

        subjects[
            subject
        ].append(
            item
        )

    for (
        subject,
        subject_items
    ) in subjects.items():

        st.subheader(
            f"{subject} · "
            f"{len(subject_items)} 題"
        )

        concepts = {}

        for item in (
            subject_items
        ):

            concept = (
                item.get(
                    "concept",
                    "未分類概念"
                )
            )

            if (
                concept
                not in concepts
            ):

                concepts[
                    concept
                ] = []

            concepts[
                concept
            ].append(
                item
            )

        for (
            concept,
            concept_items
        ) in concepts.items():

            with st.expander(
                f"{concept} · "
                f"{len(concept_items)} 題",
                expanded=False
            ):

                for item in (
                    concept_items
                ):

                    st.markdown(
                        f"### "
                        f"{item['question']}"
                    )

                    info_parts = []

                    if (
                        item.get(
                            "uncertain",
                            False
                        )
                    ):

                        info_parts.append(
                            "❓"
                        )

                    if (
                        item.get(
                            "label"
                        )
                    ):

                        info_parts.append(
                            f"🏷️ "
                            f"{item['label']}"
                        )

                    if info_parts:

                        st.write(
                            "　".join(
                                info_parts
                            )
                        )

                    render_answer_options(
                        item["options"],
                        item[
                            "correct_answer"
                        ],
                        item[
                            "user_answer"
                        ]
                    )

                    if (
                        item[
                            "user_answer"
                        ]
                        is None
                    ):

                        st.caption(
                            "本題沒有選擇答案。"
                        )

                    st.caption(
                        f"教材來源："
                        f"{item['source']}"
                    )

                    if (
                        item.get(
                            "created_at"
                        )
                    ):

                        st.caption(
                            f"紀錄時間："
                            f"{item['created_at']}"
                        )

                    st.divider()


# =========================================================
# Router
# =========================================================

show_sidebar()

if (
    st.session_state.page
    == "home"
):

    show_home()

elif (
    st.session_state.page
    == "quiz"
):

    show_quiz()

elif (
    st.session_state.page
    == "result"
):

    show_result()

elif (
    st.session_state.page
    == "mistakes"
):

    show_mistake_bank()
