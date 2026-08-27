import streamlit as st
import html
import json
import re
import hashlib
from io import BytesIO

from supabase import create_client
from pypdf import PdfReader
from openai import OpenAI


# =========================================================
# 基本設定
# =========================================================

st.set_page_config(
    page_title="Study Tool",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# Supabase
# =========================================================

@st.cache_resource
def get_supabase():
    url = str(st.secrets["SUPABASE_URL"]).strip()
    key = str(st.secrets["SUPABASE_KEY"]).strip()

    url = url.replace("\ufeff", "").replace("\u200b", "")
    key = key.replace("\ufeff", "").replace("\u200b", "")

    return create_client(url, key)


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
        return False, f"{type(error).__name__}: {str(error)}"


# =========================================================
# OpenAI
# =========================================================

@st.cache_resource
def get_openai_client():
    api_key = str(st.secrets["OPENAI_API_KEY"]).strip()
    api_key = api_key.replace("\ufeff", "").replace("\u200b", "")
    return OpenAI(api_key=api_key)


# =========================================================
# Session State
# =========================================================

default_states = {
    "page": "home",
    "question_index": 0,
    "answers": {},
    "uncertain_answers": {},
    "error_labels": {},
    "mistakes_saved": False,
    "mistake_record_ids": {},
    "label_sync_error": None,
    "document_text": None,
    "document_pages": None,
    "uploaded_filename": None,
    "uploaded_file_hash": None,

    # AI 一次處理後留下的內容
    "document_subject": None,
    "study_points": None,

    # 第一輪固定 5 題
    "generated_questions": None,
    "question_generation_error": None,
    "question_generation_stats": None,

    # 同一份 PDF 在目前 session 中曾經產生過的題目，
    # 用來避免重新產生時重複。
    "previous_questions": [],

    # 全站字體大小
    "font_size": 18,
}

for key, value in default_states.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# PDF
# =========================================================

def extract_pdf_text(file_bytes):
    reader = PdfReader(BytesIO(file_bytes))
    page_count = len(reader.pages)
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text()
            if text is None:
                text = ""
        except Exception:
            text = ""

        pages.append({
            "page": page_number,
            "text": text.strip(),
        })

    return page_count, pages


def build_document_text(pages):
    parts = []

    for page in pages:
        if not page["text"]:
            continue

        parts.append(
            f"[Page {page['page']}]\n{page['text']}"
        )

    return "\n\n".join(parts)


# =========================================================
# AI：一次整理教材重點 + 準備第一組 5 題
# =========================================================

QUIZ_SIZE = 5


def prepare_study_session_with_ai(
    document_text,
    existing_questions=None,
):
    """
    首次只呼叫一次 AI：
    1. 產生非常精簡的教材重點
    2. 同時產生第一組固定 5 題

    使用者看到教材重點時，題目其實已經準備好了，
    所以按「開始 5 題測驗」不需要再等待一次 AI。
    """

    client = get_openai_client()

    if existing_questions is None:
        existing_questions = []

    existing_summary = [
        {
            "question": item.get("question", ""),
            "concept": item.get("concept", ""),
            "source_page": item.get("source_page"),
        }
        for item in existing_questions
    ]

    schema = {
        "type": "object",
        "properties": {
            "subject": {
                "type": "string"
            },
            "study_points": {
                "type": "array",
                "minItems": 4,
                "maxItems": 7,
                "items": {
                    "type": "string"
                }
            },
            "questions": {
                "type": "array",
                "minItems": QUIZ_SIZE,
                "maxItems": QUIZ_SIZE,
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string"
                        },
                        "options": {
                            "type": "array",
                            "minItems": 4,
                            "maxItems": 4,
                            "items": {
                                "type": "string"
                            }
                        },
                        "correct_index": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 3
                        },
                        "concept": {
                            "type": "string"
                        },
                        "explanation": {
                            "type": "string"
                        },
                        "review_points": {
                            "type": "array",
                            "minItems": 2,
                            "maxItems": 4,
                            "items": {
                                "type": "string"
                            }
                        },
                        "source_page": {
                            "type": "integer",
                            "minimum": 1
                        },
                        "source_quote": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "question",
                        "options",
                        "correct_index",
                        "concept",
                        "explanation",
                        "review_points",
                        "source_page",
                        "source_quote"
                    ],
                    "additionalProperties": False
                }
            }
        },
        "required": [
            "subject",
            "study_points",
            "questions"
        ],
        "additionalProperties": False
    }

    instructions = f"""
你是一個以「先做題再學」為核心的教材學習系統。

使用者很可能還沒有讀過這份教材。
你的任務不是寫長篇摘要，而是：

A. 先整理 4～7 個非常精簡的「這份教材先掌握」重點。
B. 同時準備剛好 {QUIZ_SIZE} 題單選題。

【最重要：術語忠實規則】
這一區規則的優先級高於語句自然度。

1. 教材中出現的專有名詞一律保留原文，不得翻譯、意譯、漢化、改寫或自行換成中文名稱。
2. 只要教材使用英文術語，題幹、選項、答案、解析、複習重點都必須保留相同英文術語。
3. 如果不確定某個詞是不是專有名詞，寧可保留原文，也不要翻譯。
4. 特別包含但不限於：
   - drug / antibiotic names
   - drug classes
   - bacterial / fungal / parasitic names
   - genes
   - proteins
   - enzymes
   - receptors
   - biomarkers
   - laboratory tests
   - pathways
   - molecular names
   - abbreviations
   - syndromes / disease abbreviations
   - named mechanisms
5. 例如教材寫 `Beta-lactam`，輸出必須仍是 `Beta-lactam`，不得寫成 `Beta-內醯胺`、`β-內醯胺` 或其他中文譯名。
6. 教材寫 `vancomycin`，不得改成中文藥名。
7. 教材寫 `Staphylococcus aureus`，不得自行改成中文菌名。
8. 教材寫 `MRSA`，不得自行翻譯或改寫；除非教材本身同時提供完整名稱且題目確實需要。
9. 一般敘述與問句可以用繁體中文，但專業名詞本體必須維持教材原文。
10. 不要為了讓中文句子更順，而翻譯任何專有名詞。

【教材重點規則】
1. 每個重點用一句短句表達。
2. 優先列出理解教材最有幫助的核心概念、差異、機轉、流程或判讀原則。
3. 不要寫成長篇摘要。
4. 不要宣稱「最常考」「高頻考點」，除非教材本身明確這樣說。
5. 只能依照教材內容，不得補充外部知識。
6. 所有專有名詞都必須遵守上方「術語忠實規則」。

【出題規則】
1. 所有題目、答案、解析都只能根據提供的教材。
2. 不可以用外部知識補答案。
3. 每題只能有一個明確正確答案。
4. 每題必須有四個不同選項。
5. distractors 要合理，但不能讓兩個答案同時成立。
6. correct_index 使用 0、1、2、3。
7. concept 是該題真正測驗的核心概念。
8. 優先讓 {QUIZ_SIZE} 題涵蓋不同概念，不要大量重複同一件事。
9. source_page 必須是教材中的實際 Page 編號。
10. source_quote 必須逐字摘自該頁教材。
11. source_quote 必須足以支持正確答案。
12. source_quote 不可以改寫。
13. explanation 要解釋正確答案，但不可加入教材外資訊。
14. review_points 為 2～4 個短而有用的複習重點。
15. 如果某個概念無法產生無歧義題目，就換另一個概念。
16. 題幹、四個選項、正確答案、concept、explanation、review_points 中的所有專有名詞都必須遵守「術語忠實規則」。

【避免重複】
以下是同一份教材在目前 session 已經產生過的題目。
本次不得重複相同題幹，也不要只是換句話說測完全相同的內容：

{json.dumps(existing_summary, ensure_ascii=False)}
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        instructions=instructions,
        input=(
            "以下是使用者上傳教材：\n\n"
            + document_text
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": "study_session",
                "strict": True,
                "schema": schema
            }
        }
    )

    return json.loads(
        response.output_text
    )


# =========================================================
# AI 題目生成
# =========================================================

def generate_questions_with_ai(
    document_text,
    subject,
    study_points,
    question_count,
    existing_questions=None,
):
    """
    只有第一組題目被 Python 驗證淘汰時才呼叫。
    一次批量補足缺額，不逐題驗證。
    """

    client = get_openai_client()

    if existing_questions is None:
        existing_questions = []

    existing_summary = [
        {
            "question": item.get("question", ""),
            "concept": item.get("concept", ""),
            "source_page": item.get("source_page"),
        }
        for item in existing_questions
    ]

    schema = {
        "type": "object",
        "properties": {
            "questions": {
                "type": "array",
                "minItems": question_count,
                "maxItems": question_count,
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string"
                        },
                        "options": {
                            "type": "array",
                            "minItems": 4,
                            "maxItems": 4,
                            "items": {
                                "type": "string"
                            }
                        },
                        "correct_index": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 3
                        },
                        "concept": {
                            "type": "string"
                        },
                        "explanation": {
                            "type": "string"
                        },
                        "review_points": {
                            "type": "array",
                            "minItems": 2,
                            "maxItems": 4,
                            "items": {
                                "type": "string"
                            }
                        },
                        "source_page": {
                            "type": "integer",
                            "minimum": 1
                        },
                        "source_quote": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "question",
                        "options",
                        "correct_index",
                        "concept",
                        "explanation",
                        "review_points",
                        "source_page",
                        "source_quote"
                    ],
                    "additionalProperties": False
                }
            }
        },
        "required": [
            "questions"
        ],
        "additionalProperties": False
    }

    instructions = f"""
你是一個嚴格的教材測驗補題系統。

目前只缺 {question_count} 題，請產生剛好 {question_count} 題。

教材後台分類：
{subject}

這份教材先掌握：
{json.dumps(study_points, ensure_ascii=False)}

【最重要：術語忠實規則】
1. 教材中的專有名詞一律保留原文，不得翻譯、意譯、漢化或改寫。
2. 如果教材使用英文 drug name、antibiotic class、菌名、gene、protein、enzyme、receptor、marker、test、pathway、molecule 或 abbreviation，就必須維持教材原本英文寫法。
3. 如果不確定是不是專有名詞，保留原文。
4. 例如 `Beta-lactam` 必須保持 `Beta-lactam`，不得輸出 `Beta-內醯胺` 或 `β-內醯胺`。
5. 一般句子可以是繁體中文，但專有名詞本體不可翻譯。

【規則】
1. 所有題目、答案、解析只能根據教材。
2. 不得使用外部知識。
3. 每題只有一個明確正確答案。
4. 四個選項必須不同。
5. correct_index 使用 0、1、2、3。
6. source_page 必須是教材實際 Page 編號。
7. source_quote 必須逐字摘自該頁，且足以支持答案。
8. 不要改寫 source_quote。
9. explanation 與 review_points 都不得加入教材外資訊。
10. 題幹、選項、答案、解析、複習重點的專有名詞全部遵守「術語忠實規則」。
11. 不要重複以下已經通過的題目，也不要只換句話說：

{json.dumps(existing_summary, ensure_ascii=False)}
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        instructions=instructions,
        input=(
            "以下是教材全文：\n\n"
            + document_text
        ),
        text={
            "format": {
                "type": "json_schema",
                "name": "quiz_refill",
                "strict": True,
                "schema": schema
            }
        }
    )

    result = json.loads(
        response.output_text
    )

    return result["questions"]


# =========================================================
# Grounding 驗證
# =========================================================

def normalize_text(text):
    text = str(text)
    return re.sub(r"\s+", "", text)


def question_fingerprint(
    question_text
):
    """
    免費的 deterministic 去重：
    移除空白與常見標點後比較題幹。
    """

    normalized = normalize_text(
        question_text
    )

    normalized = re.sub(
        r"[，。！？；：、,.!?;:()（）\\[\\]【】「」『』\\\"'`]",
        "",
        normalized
    )

    return normalized.lower()


def remove_duplicate_questions(
    candidate_questions,
    existing_questions=None,
):
    """
    避免補題時把已通過的題目重新塞回來。
    """

    if existing_questions is None:
        existing_questions = []

    seen = {
        question_fingerprint(
            item.get("question", "")
        )
        for item in existing_questions
    }

    unique_questions = []
    rejected = []

    for index, question in enumerate(
        candidate_questions,
        start=1,
    ):
        fingerprint = question_fingerprint(
            question.get("question", "")
        )

        if (
            not fingerprint
            or fingerprint in seen
        ):
            rejected.append({
                "number": index,
                "reasons": [
                    "題目與已通過題目重複"
                ]
            })
            continue

        seen.add(fingerprint)
        unique_questions.append(
            question
        )

    return unique_questions, rejected


def validate_and_refill_quiz(
    initial_questions,
    document_text,
    subject,
    study_points,
    pages,
    filename,
    target_count=QUIZ_SIZE,
    max_refill_rounds=2,
):
    """
    1. 先驗證首次同一個 AI request 產生的 5 題。
    2. 若有題目被 Python 淘汰，只批量補缺額。
    3. 最多補 2 輪，避免無限 API 呼叫。
    """

    accepted = []
    all_rejections = []
    generation_rounds = []

    # -----------------------------------------------------
    # 第 0 輪：首次 AI request 已經產生好的題目
    # -----------------------------------------------------

    (
        non_duplicate_questions,
        duplicate_rejections,
    ) = (
        remove_duplicate_questions(
            initial_questions,
            existing_questions=[],
        )
    )

    (
        valid_questions,
        validation_rejections,
    ) = (
        validate_generated_questions(
            non_duplicate_questions,
            pages,
            filename,
            subject,
        )
    )

    accepted.extend(
        valid_questions[
            :target_count
        ]
    )

    initial_rejections = (
        duplicate_rejections
        + validation_rejections
    )

    all_rejections.extend(
        [
            {
                "round": 0,
                "number": item["number"],
                "reasons": item["reasons"],
            }
            for item in initial_rejections
        ]
    )

    generation_rounds.append({
        "round": 0,
        "requested": len(initial_questions),
        "accepted": len(accepted),
        "rejected": len(initial_rejections),
        "total_accepted": len(accepted),
    })

    # -----------------------------------------------------
    # 缺幾題就一次補幾題
    # -----------------------------------------------------

    for refill_round in range(
        1,
        max_refill_rounds + 1,
    ):
        missing_count = (
            target_count
            - len(accepted)
        )

        if missing_count <= 0:
            break

        raw_questions = (
            generate_questions_with_ai(
                document_text=document_text,
                subject=subject,
                study_points=study_points,
                question_count=missing_count,
                existing_questions=accepted,
            )
        )

        (
            non_duplicate_questions,
            duplicate_rejections,
        ) = (
            remove_duplicate_questions(
                raw_questions,
                existing_questions=accepted,
            )
        )

        (
            valid_questions,
            validation_rejections,
        ) = (
            validate_generated_questions(
                non_duplicate_questions,
                pages,
                filename,
                subject,
            )
        )

        remaining_slots = (
            target_count
            - len(accepted)
        )

        newly_accepted = (
            valid_questions[
                :remaining_slots
            ]
        )

        accepted.extend(
            newly_accepted
        )

        round_rejections = (
            duplicate_rejections
            + validation_rejections
        )

        all_rejections.extend(
            [
                {
                    "round": refill_round,
                    "number": item["number"],
                    "reasons": item["reasons"],
                }
                for item in round_rejections
            ]
        )

        generation_rounds.append({
            "round": refill_round,
            "requested": missing_count,
            "accepted": len(newly_accepted),
            "rejected": len(round_rejections),
            "total_accepted": len(accepted),
        })

    return (
        accepted[:target_count],
        all_rejections,
        generation_rounds,
    )



def validate_generated_questions(
    raw_questions,
    pages,
    filename,
    subject,
):
    valid_questions = []
    rejected_questions = []

    page_lookup = {
        page["page"]: page["text"]
        for page in pages
    }

    for index, question in enumerate(
        raw_questions,
        start=1,
    ):
        reasons = []

        options = question.get("options", [])
        correct_index = question.get("correct_index")
        source_page = question.get("source_page")
        source_quote = question.get("source_quote", "")

        if len(options) != 4:
            reasons.append("選項數量不是 4")

        normalized_options = [
            normalize_text(option)
            for option in options
        ]

        if (
            len(set(normalized_options))
            != len(normalized_options)
        ):
            reasons.append("存在重複選項")

        if (
            not isinstance(correct_index, int)
            or correct_index not in [0, 1, 2, 3]
        ):
            reasons.append("正確答案 index 無效")

        if source_page not in page_lookup:
            reasons.append("來源頁碼不存在")

        else:
            normalized_page = normalize_text(
                page_lookup[source_page]
            )

            normalized_quote = normalize_text(
                source_quote
            )

            if not normalized_quote:
                reasons.append("來源證據為空")

            elif normalized_quote not in normalized_page:
                reasons.append(
                    "來源證據無法在指定頁面找到"
                )

        if not reasons:
            valid_questions.append({
                "question": question["question"],
                "options": options,
                "answer": correct_index,
                "subject": subject,
                "concept": question["concept"],
                "review_type": "bullets",
                "review_points": question["review_points"],
                "explanation": question["explanation"],
                "source_page": source_page,
                "source_quote": source_quote,
                "source": (
                    f"{filename} · Page {source_page}"
                )
            })

        else:
            rejected_questions.append({
                "number": index,
                "reasons": reasons,
            })

    return valid_questions, rejected_questions


# =========================================================
# 目前測驗題目
# =========================================================

def get_questions():
    questions = st.session_state.generated_questions

    if questions is None:
        return []

    return questions


# =========================================================
# 字體大小控制
# =========================================================

FONT_SIZE_MIN = 14
FONT_SIZE_MAX = 26
FONT_SIZE_STEP = 2


def decrease_font_size():
    st.session_state.font_size = max(
        FONT_SIZE_MIN,
        st.session_state.font_size - FONT_SIZE_STEP,
    )


def increase_font_size():
    st.session_state.font_size = min(
        FONT_SIZE_MAX,
        st.session_state.font_size + FONT_SIZE_STEP,
    )


def apply_font_size():
    """
    套用全站字體大小。
    文字、按鈕、選項、sidebar 都會跟著調整。
    """

    size = st.session_state.font_size

    st.markdown(
        f"""
        <style>

        /* 一般文字 */
        .stApp p,
        .stApp li,
        .stApp label,
        .stApp span,
        .stApp div[data-testid="stMarkdownContainer"] p,
        .stApp div[data-testid="stMarkdownContainer"] li {{
            font-size: {size}px !important;
            line-height: 1.65 !important;
        }}

        /* 按鈕 */
        .stApp button p,
        .stApp button div,
        .stApp button span {{
            font-size: {size}px !important;
        }}

        /* radio / checkbox */
        .stApp div[role="radiogroup"] label p,
        .stApp div[data-testid="stCheckbox"] label p {{
            font-size: {size}px !important;
        }}

        /* 輸入欄位 */
        .stApp input,
        .stApp textarea {{
            font-size: {size}px !important;
        }}

        /* caption */
        .stApp div[data-testid="stCaptionContainer"] p {{
            font-size: {max(FONT_SIZE_MIN, size - 2)}px !important;
        }}

        /* 標題依比例放大 */
        .stApp h1 {{
            font-size: {size + 18}px !important;
        }}

        .stApp h2 {{
            font-size: {size + 12}px !important;
        }}

        .stApp h3 {{
            font-size: {size + 8}px !important;
        }}

        /* metric */
        .stApp div[data-testid="stMetricValue"] {{
            font-size: {size + 10}px !important;
        }}

        .stApp div[data-testid="stMetricLabel"] p {{
            font-size: {size}px !important;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# Sidebar
# =========================================================

def show_sidebar():
    with st.sidebar:
        st.title("📚 Study Tool")

        if st.button(
            "首頁",
            use_container_width=True,
        ):
            st.session_state.page = "home"
            st.rerun()

        if st.button(
            "錯題庫",
            use_container_width=True,
        ):
            st.session_state.page = "mistakes"
            st.rerun()

        st.button(
            "弱點分析",
            use_container_width=True,
            disabled=True,
        )

        st.divider()

        # =================================================
        # 字體大小
        # =================================================

        st.markdown("### 字體大小")

        font_col1, font_col2, font_col3 = st.columns(
            [1, 1.4, 1]
        )

        with font_col1:
            st.button(
                "A−",
                on_click=decrease_font_size,
                disabled=(
                    st.session_state.font_size
                    <= FONT_SIZE_MIN
                ),
                use_container_width=True,
            )

        with font_col2:
            st.markdown(
                f"<div style='text-align:center; padding-top:8px;'>"
                f"{st.session_state.font_size}px"
                f"</div>",
                unsafe_allow_html=True,
            )

        with font_col3:
            st.button(
                "A+",
                on_click=increase_font_size,
                disabled=(
                    st.session_state.font_size
                    >= FONT_SIZE_MAX
                ),
                use_container_width=True,
            )

        st.caption(
            f"可調範圍：{FONT_SIZE_MIN}px ～ {FONT_SIZE_MAX}px"
        )

        st.divider()

        connected, error = test_database_connection()

        if connected:
            st.success("Database connected")

        else:
            st.error("Database connection failed")

            with st.expander("查看錯誤"):
                st.code(error)

        st.caption("Prototype v0.12")


# =========================================================
# 彩色答案
# =========================================================

def render_answer_options(
    options,
    correct_answer,
    user_answer,
):
    labels = ["A", "B", "C", "D"]

    for label, option in zip(
        labels,
        options,
    ):
        is_correct = option == correct_answer
        is_user_answer = option == user_answer

        background = "rgba(128,128,128,0.08)"
        border = "1px solid rgba(128,128,128,0.25)"

        if is_correct:
            background = "rgba(46,204,113,0.18)"
            border = "1px solid rgba(46,204,113,0.55)"

        if is_user_answer and not is_correct:
            background = "rgba(231,76,60,0.18)"
            border = "1px solid rgba(231,76,60,0.55)"

        if is_user_answer and is_correct:
            background = "rgba(46,204,113,0.18)"
            border = "2px solid rgba(231,76,60,0.70)"

        safe_option = html.escape(str(option))

        st.markdown(
            f"""
            <div style="
                background:{background};
                border:{border};
                border-radius:10px;
                padding:12px 16px;
                margin-bottom:9px;
            ">
                <strong>{label}.</strong>
                {safe_option}
            </div>
            """,
            unsafe_allow_html=True,
        )


# =========================================================
# 答題 State
# =========================================================

def save_answer(question_index):
    key = f"radio_{question_index}"

    if key in st.session_state:
        st.session_state.answers[
            question_index
        ] = st.session_state[key]


def save_uncertain(question_index):
    key = f"uncertain_{question_index}"

    if key in st.session_state:
        value = st.session_state[key]

        st.session_state.uncertain_answers[
            question_index
        ] = value

        if value:
            if (
                question_index
                not in st.session_state.error_labels
            ):
                st.session_state.error_labels[
                    question_index
                ] = "觀念不熟"


# =========================================================
# 結果頁 Label → Supabase
# =========================================================

def save_error_label(question_index):
    key = f"error_label_{question_index}"

    if key not in st.session_state:
        return

    new_label = st.session_state[key]

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
            "找不到對應的資料庫紀錄。"
        )
        return

    try:
        supabase = get_supabase()

        (
            supabase
            .table("mistakes")
            .update({
                "label": new_label
            })
            .eq(
                "id",
                record_id
            )
            .execute()
        )

        st.session_state.label_sync_error = None

    except Exception as error:
        st.session_state.label_sync_error = (
            f"{type(error).__name__}: {str(error)}"
        )


# =========================================================
# 錯題庫 Label → Supabase
# =========================================================

def save_bank_error_label(record_id):
    key = f"bank_label_{record_id}"

    if key not in st.session_state:
        return

    new_label = st.session_state[key]

    try:
        supabase = get_supabase()

        (
            supabase
            .table("mistakes")
            .update({
                "label": new_label
            })
            .eq(
                "id",
                record_id
            )
            .execute()
        )

    except Exception as error:
        st.session_state.label_sync_error = (
            f"{type(error).__name__}: {str(error)}"
        )


# =========================================================
# Supabase 錯題
# =========================================================

def save_mistakes_to_database():
    if st.session_state.mistakes_saved:
        return

    questions = get_questions()
    supabase = get_supabase()

    st.session_state.mistake_record_ids = {}

    for i, question in enumerate(questions):
        user_answer = (
            st.session_state
            .answers
            .get(i)
        )

        uncertain = (
            st.session_state
            .uncertain_answers
            .get(i, False)
        )

        correct_answer = (
            question["options"][
                question["answer"]
            ]
        )

        is_correct = (
            user_answer == correct_answer
        )

        needs_review = (
            (not is_correct)
            or uncertain
        )

        if not needs_review:
            continue

        row = {
            "subject": question["subject"],
            "concept": question["concept"],
            "question": question["question"],
            "options": question["options"],
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "uncertain": uncertain,
            "is_correct": is_correct,
            "label": (
                st.session_state
                .error_labels
                .get(i)
            ),
            "source": question["source"],

            # 檢討內容也永久保存，
            # 讓錯題庫可以完整重現結果頁的解析。
            "explanation": question.get(
                "explanation",
                ""
            ),
            "review_points": question.get(
                "review_points",
                []
            ),
            "source_quote": question.get(
                "source_quote",
                ""
            ),
        }

        response = (
            supabase
            .table("mistakes")
            .insert(row)
            .execute()
        )

        if response.data and len(response.data) > 0:
            st.session_state.mistake_record_ids[
                i
            ] = response.data[0]["id"]

    st.session_state.mistakes_saved = True


def load_mistakes_from_database():
    supabase = get_supabase()

    response = (
        supabase
        .table("mistakes")
        .select("*")
        .order(
            "created_at",
            desc=True,
        )
        .execute()
    )

    return response.data


# =========================================================
# 結束測驗
# =========================================================

@st.dialog("結束測驗")
def finish_quiz_dialog():
    questions = get_questions()
    unanswered = []

    for i in range(len(questions)):
        answer = (
            st.session_state
            .answers
            .get(i)
        )

        uncertain = (
            st.session_state
            .uncertain_answers
            .get(i, False)
        )

        if answer is None and not uncertain:
            unanswered.append(i + 1)

    if unanswered:
        question_list = "、".join(
            [
                f"第 {number} 題"
                for number in unanswered
            ]
        )

        st.warning(
            f"你還有未作答的題目：{question_list}"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "返回測驗",
                use_container_width=True,
            ):
                st.rerun()

        with col2:
            if st.button(
                "仍然結束",
                use_container_width=True,
            ):
                try:
                    save_mistakes_to_database()

                except Exception as error:
                    st.error("錯題儲存失敗")
                    st.code(str(error))
                    return

                st.session_state.page = "result"
                st.rerun()

    else:
        st.success("所有題目皆已完成。")

        if st.button(
            "查看結果",
            use_container_width=True,
        ):
            try:
                save_mistakes_to_database()

            except Exception as error:
                st.error("錯題儲存失敗")
                st.code(str(error))
                return

            st.session_state.page = "result"
            st.rerun()


# =========================================================
# 開始新測驗
# =========================================================

def reset_quiz_state():
    questions = get_questions()

    st.session_state.question_index = 0
    st.session_state.answers = {}
    st.session_state.uncertain_answers = {}
    st.session_state.error_labels = {}
    st.session_state.mistakes_saved = False
    st.session_state.mistake_record_ids = {}
    st.session_state.label_sync_error = None

    for i in range(len(questions)):
        for key in [
            f"radio_{i}",
            f"uncertain_{i}",
            f"error_label_{i}",
        ]:
            if key in st.session_state:
                del st.session_state[key]


# =========================================================
# 首頁
# =========================================================

def show_home():
    st.title("📚 把教材丟進來，先做 5 題")

    st.write(
        "不用先把整份講義讀完。"
        "先用 5 題找出你還不熟的地方。"
    )

    st.divider()

    uploaded_file = st.file_uploader(
        "上傳 PDF",
        type=["pdf"],
    )

    if uploaded_file is None:
        return

    file_bytes = uploaded_file.getvalue()

    file_hash = (
        hashlib.sha256(
            file_bytes
        )
        .hexdigest()
    )

    # =====================================================
    # 換了一份教材
    # =====================================================

    if (
        st.session_state.uploaded_file_hash
        != file_hash
    ):
        st.session_state.uploaded_file_hash = (
            file_hash
        )

        st.session_state.uploaded_filename = (
            uploaded_file.name
        )

        st.session_state.document_subject = None
        st.session_state.study_points = None
        st.session_state.generated_questions = None
        st.session_state.question_generation_error = None
        st.session_state.question_generation_stats = None
        st.session_state.previous_questions = []

    # =====================================================
    # PDF parsing 在後台進行
    # 不把頁數、字元數、文字預覽等工程資訊顯示給使用者
    # =====================================================

    try:
        page_count, pages = (
            extract_pdf_text(
                file_bytes
            )
        )

    except Exception:
        st.error(
            "這份 PDF 無法讀取，請換一份檔案再試一次。"
        )
        return

    document_text = (
        build_document_text(
            pages
        )
    )

    st.session_state.document_pages = pages
    st.session_state.document_text = document_text

    pages_with_text = sum(
        1
        for page in pages
        if page["text"]
    )

    if pages_with_text == 0:
        st.warning(
            "這份 PDF 沒有可讀取的文字。"
            "如果是掃描檔，目前這個版本還無法處理。"
        )
        return

    st.divider()

    # =====================================================
    # 還沒處理：
    # 一個按鈕一次完成教材重點 + 第一組 5 題
    # =====================================================

    if (
        st.session_state.generated_questions
        is None
    ):
        if st.button(
            "AI 分析教材",
            use_container_width=True,
            type="primary",
        ):
            try:
                with st.spinner(
                    "正在整理教材並準備 5 題..."
                ):
                    package = (
                        prepare_study_session_with_ai(
                            document_text,
                            existing_questions=(
                                st.session_state.previous_questions
                            ),
                        )
                    )

                    subject = package[
                        "subject"
                    ]

                    study_points = package[
                        "study_points"
                    ]

                    (
                        final_questions,
                        all_rejections,
                        generation_rounds,
                    ) = (
                        validate_and_refill_quiz(
                            initial_questions=package[
                                "questions"
                            ],
                            document_text=document_text,
                            subject=subject,
                            study_points=study_points,
                            pages=pages,
                            filename=uploaded_file.name,
                            target_count=QUIZ_SIZE,
                            max_refill_rounds=2,
                        )
                    )

                st.session_state.document_subject = (
                    subject
                )

                st.session_state.study_points = (
                    study_points
                )

                st.session_state.generated_questions = (
                    final_questions
                )

                # 記住這一組，之後同一 session 重新產生時避免重複
                st.session_state.previous_questions.extend(
                    final_questions
                )

                st.session_state.question_generation_stats = (
                    generation_rounds
                )

                if all_rejections:
                    rejected_text = []

                    for item in all_rejections:
                        reasons = "、".join(
                            item["reasons"]
                        )

                        rejected_text.append(
                            f"round={item['round']}, "
                            f"question={item['number']}: "
                            f"{reasons}"
                        )

                    # 只留在 session 方便之後 debug，
                    # 不在正常使用者畫面展示。
                    st.session_state.question_generation_error = (
                        "\n".join(
                            rejected_text
                        )
                    )

                else:
                    st.session_state.question_generation_error = None

                st.rerun()

            except Exception as error:
                st.error(
                    "AI 處理失敗，請稍後再試一次。"
                )

                with st.expander(
                    "查看技術錯誤"
                ):
                    st.code(
                        f"{type(error).__name__}: "
                        f"{str(error)}"
                    )

        return

    # =====================================================
    # 已經處理完成
    # =====================================================

    study_points = (
        st.session_state.study_points
        or []
    )

    generated_questions = (
        get_questions()
    )

    if study_points:
        st.subheader(
            "這份教材先掌握"
        )

        for point in study_points:
            st.markdown(
                f"- {point}"
            )

    st.divider()

    if not generated_questions:
        st.error(
            "這次沒有題目通過來源驗證，"
            "請重新分析一次。"
        )

        if st.button(
            "重新分析教材",
            use_container_width=True,
        ):
            st.session_state.document_subject = None
            st.session_state.study_points = None
            st.session_state.generated_questions = None
            st.session_state.question_generation_error = None
            st.session_state.question_generation_stats = None
            st.rerun()

        return

    if (
        len(generated_questions)
        < QUIZ_SIZE
    ):
        st.warning(
            f"這次有 {len(generated_questions)} 題通過驗證，"
            "先從這些題目開始。"
        )

    if st.button(
        f"開始 {len(generated_questions)} 題測驗",
        use_container_width=True,
        type="primary",
    ):
        reset_quiz_state()

        st.session_state.page = (
            "quiz"
        )

        st.rerun()

    if st.button(
        "換一組新的 5 題",
        use_container_width=True,
    ):
        # 保留 previous_questions，
        # 只清掉目前這一組，讓同一份 PDF 重新產生不同題目。
        st.session_state.document_subject = None
        st.session_state.study_points = None
        st.session_state.generated_questions = None
        st.session_state.question_generation_error = None
        st.session_state.question_generation_stats = None
        st.rerun()


# =========================================================
# Quiz
# =========================================================

def show_quiz():
    questions = get_questions()

    if not questions:
        st.error(
            "目前沒有可用的測驗題目。"
        )
        return

    current = st.session_state.question_index
    question = questions[current]

    top_left, top_right = st.columns(
        [7, 1.4]
    )

    with top_left:
        st.markdown(
            f"""
            <div style="
                padding-top:8px;
                font-size:18px;
                font-weight:600;
            ">
                Question {current + 1}
                /
                {len(questions)}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with top_right:
        if st.button(
            "結束測驗",
            use_container_width=True,
            key=f"finish_top_{current}",
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

        if saved_answer is not None:
            st.session_state[
                radio_key
            ] = saved_answer

    st.radio(
        "請選擇答案",
        question["options"],
        index=None,
        key=radio_key,
        on_change=save_answer,
        args=(current,),
    )

    uncertain_key = (
        f"uncertain_{current}"
    )

    if (
        uncertain_key
        not in st.session_state
    ):
        st.session_state[
            uncertain_key
        ] = (
            st.session_state
            .uncertain_answers
            .get(
                current,
                False,
            )
        )

    st.checkbox(
        "❓ 我不確定",
        key=uncertain_key,
        on_change=save_uncertain,
        args=(current,),
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
            False,
        )
    )

    if answer_exists and uncertain:
        st.caption(
            "已作答 · ❓ 不確定"
        )

    elif answer_exists:
        st.caption("已作答")

    elif uncertain:
        st.caption(
            "❓ 已標記為不確定"
        )

    st.divider()

    total = len(questions)

    if current == 0:
        empty_col, next_col = (
            st.columns(2)
        )

        with next_col:
            if current < total - 1:
                if st.button(
                    "下一題 →",
                    use_container_width=True,
                    key=f"next_{current}",
                ):
                    st.session_state.question_index += 1
                    st.rerun()

    elif current == total - 1:
        prev_col, empty_col = (
            st.columns(2)
        )

        with prev_col:
            if st.button(
                "← 上一題",
                use_container_width=True,
                key=f"prev_{current}",
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
                key=f"prev_{current}",
            ):
                st.session_state.question_index -= 1
                st.rerun()

        with next_col:
            if st.button(
                "下一題 →",
                use_container_width=True,
                key=f"next_{current}",
            ):
                st.session_state.question_index += 1
                st.rerun()


# =========================================================
# Result Review
# =========================================================

def show_review_item(question_index):
    questions = get_questions()
    question = questions[question_index]

    user_answer = (
        st.session_state
        .answers
        .get(question_index)
    )

    uncertain = (
        st.session_state
        .uncertain_answers
        .get(
            question_index,
            False,
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

    if is_correct and uncertain:
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
        expanded=False,
    ):
        st.markdown(
            f"### {question['question']}"
        )

        render_answer_options(
            question["options"],
            correct_answer,
            user_answer,
        )

        if user_answer is None:
            st.caption(
                "你沒有選擇答案，"
                "但曾標記 ❓。"
            )

        st.divider()

        st.markdown("### 核心觀念")
        st.write(question["concept"])

        st.markdown("### 為什麼？")
        st.write(question["explanation"])

        st.markdown("### 複習重點")

        for point in question[
            "review_points"
        ]:
            st.markdown(
                f"- {point}"
            )

        st.markdown(
            "### 📖 教材根據"
        )

        st.caption(
            question["source"]
        )

        st.info(
            question["source_quote"]
        )

        st.divider()

        st.markdown(
            "**你認為這次需要檢討的原因是？**"
        )

        label_options = [
            "粗心大意",
            "觀念不熟",
            "完全沒看過",
        ]

        saved_label = (
            st.session_state
            .error_labels
            .get(question_index)
        )

        if saved_label in label_options:
            label_index = (
                label_options.index(
                    saved_label
                )
            )

        else:
            label_index = None

        label_key = (
            f"error_label_"
            f"{question_index}"
        )

        st.radio(
            "錯誤分類",
            label_options,
            index=label_index,
            horizontal=True,
            key=label_key,
            on_change=save_error_label,
            args=(question_index,),
            label_visibility="collapsed",
        )


# =========================================================
# Result
# =========================================================

def show_result():
    questions = get_questions()

    if not questions:
        st.error("沒有測驗資料。")
        return

    st.title("測驗完成")

    # =====================================================
    # 計算分數
    # =====================================================

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

    total = len(questions)

    percentage = round(
        correct_count
        / total
        * 100
    )

    st.subheader(
        f"{correct_count} / "
        f"{total}"
        f"（{percentage}%）"
    )

    # =====================================================
    # 只整理需要檢討的題目
    # 不再另外顯示「答題結果」
    # =====================================================

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
            .get(i, False)
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
            (not is_correct)
            or uncertain
        ):
            review_questions.append(i)

    if review_questions:
        st.divider()
        st.subheader("需要檢討")

        for question_index in (
            review_questions
        ):
            show_review_item(
                question_index
            )

    else:
        st.success(
            "這次沒有需要檢討的題目。"
        )

    st.divider()

    nav1, nav2 = st.columns(2)

    with nav1:
        if st.button(
            "查看錯題庫",
            use_container_width=True,
        ):
            st.session_state.page = "mistakes"
            st.rerun()

    with nav2:
        if st.button(
            "回首頁",
            use_container_width=True,
        ):
            st.session_state.page = "home"
            st.rerun()


# =========================================================
# Mistake Bank
# =========================================================

def show_mistake_bank():
    st.title("📘 錯題庫")

    try:
        mistake_bank = (
            load_mistakes_from_database()
        )

    except Exception as error:
        st.error("無法讀取錯題庫")
        st.code(str(error))
        return

    if not mistake_bank:
        st.info(
            "目前還沒有錯題紀錄。"
        )
        return

    # -----------------------------------------------------
    # 統計
    #
    # 每一筆錯題只能有一個 label。
    # 修改 label 時是 UPDATE 同一筆資料，
    # 所以不會重複計算。
    # -----------------------------------------------------

    total = len(mistake_bank)

    careless = sum(
        1
        for item in mistake_bank
        if item.get("label")
        == "粗心大意"
    )

    unfamiliar = sum(
        1
        for item in mistake_bank
        if item.get("label")
        == "觀念不熟"
    )

    unseen = sum(
        1
        for item in mistake_bank
        if item.get("label")
        == "完全沒看過"
    )

    unclassified = sum(
        1
        for item in mistake_bank
        if not item.get("label")
    )

    col1, col2, col3, col4, col5 = (
        st.columns(5)
    )

    col1.metric(
        "需複習",
        total,
    )

    col2.metric(
        "粗心大意",
        careless,
    )

    col3.metric(
        "觀念不熟",
        unfamiliar,
    )

    col4.metric(
        "完全沒看過",
        unseen,
    )

    col5.metric(
        "未分類",
        unclassified,
    )

    st.divider()

    subjects = {}

    for item in mistake_bank:
        subject = item.get(
            "subject",
            "未分類",
        )

        if subject not in subjects:
            subjects[subject] = []

        subjects[subject].append(
            item
        )

    for (
        subject,
        subject_items,
    ) in subjects.items():
        st.subheader(
            f"{subject} · "
            f"{len(subject_items)} 題"
        )

        concepts = {}

        for item in subject_items:
            concept = item.get(
                "concept",
                "未分類概念",
            )

            if concept not in concepts:
                concepts[concept] = []

            concepts[concept].append(
                item
            )

        for (
            concept,
            concept_items,
        ) in concepts.items():
            with st.expander(
                f"{concept} · "
                f"{len(concept_items)} 題",
                expanded=False,
            ):
                for item in concept_items:
                    st.markdown(
                        f"### "
                        f"{item['question']}"
                    )

                    if item.get(
                        "uncertain",
                        False,
                    ):
                        st.write("❓")

                    render_answer_options(
                        item["options"],
                        item["correct_answer"],
                        item["user_answer"],
                    )

                    if (
                        item["user_answer"]
                        is None
                    ):
                        st.caption(
                            "本題沒有選擇答案。"
                        )

                    st.divider()

                    # =====================================
                    # 完整檢討內容
                    # =====================================

                    st.markdown("### 核心觀念")
                    st.write(
                        item.get(
                            "concept",
                            "未分類概念"
                        )
                    )

                    explanation = item.get(
                        "explanation"
                    )

                    if explanation:
                        st.markdown("### 為什麼？")
                        st.write(
                            explanation
                        )

                    review_points = item.get(
                        "review_points"
                    )

                    if review_points:
                        st.markdown("### 複習重點")

                        for point in review_points:
                            st.markdown(
                                f"- {point}"
                            )

                    source_quote = item.get(
                        "source_quote"
                    )

                    st.markdown("### 📖 教材根據")

                    st.caption(
                        f"教材來源："
                        f"{item['source']}"
                    )

                    if source_quote:
                        st.info(
                            source_quote
                        )

                    if item.get(
                        "created_at"
                    ):
                        st.caption(
                            f"紀錄時間："
                            f"{item['created_at']}"
                        )

                    # =====================================
                    # 錯題庫也可修改原因
                    # =====================================

                    st.markdown(
                        "**錯誤原因**"
                    )

                    label_options = [
                        "粗心大意",
                        "觀念不熟",
                        "完全沒看過",
                    ]

                    saved_label = item.get(
                        "label"
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

                    record_id = item["id"]

                    st.radio(
                        "錯誤原因",
                        label_options,
                        index=label_index,
                        horizontal=True,
                        key=(
                            f"bank_label_"
                            f"{record_id}"
                        ),
                        on_change=save_bank_error_label,
                        args=(record_id,),
                        label_visibility="collapsed",
                    )

                    st.divider()


# =========================================================
# Router
# =========================================================

apply_font_size()
show_sidebar()

if st.session_state.page == "home":
    show_home()

elif st.session_state.page == "quiz":
    show_quiz()

elif st.session_state.page == "result":
    show_result()

elif st.session_state.page == "mistakes":
    show_mistake_bank()
