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
    "document_analysis": None,
    "document_text": None,
    "document_pages": None,
    "uploaded_filename": None,
    "uploaded_file_hash": None,
    "generated_questions": None,
    "question_generation_error": None,
    "question_generation_stats": None,
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


def create_pdf_preview(
    pages,
    max_pages=3,
    max_chars_per_page=1500,
):
    preview_parts = []

    for page_data in pages[:max_pages]:
        page_number = page_data["page"]
        text = page_data["text"]

        if not text:
            text = "（此頁未擷取到可讀取文字）"

        if len(text) > max_chars_per_page:
            text = text[:max_chars_per_page] + "..."

        preview_parts.append(
            f"--- 第 {page_number} 頁 ---\n{text}"
        )

    return "\n\n".join(preview_parts)


# =========================================================
# AI 教材分析
# =========================================================

def analyze_document_with_ai(document_text):
    client = get_openai_client()

    schema = {
        "type": "object",
        "properties": {
            "subject": {
                "type": "string"
            },
            "summary": {
                "type": "string"
            },
            "main_topics": {
                "type": "array",
                "items": {
                    "type": "string"
                }
            },
            "knowledge_units": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string"
                        },
                        "description": {
                            "type": "string"
                        },
                        "importance": {
                            "type": "string",
                            "enum": [
                                "high",
                                "medium",
                                "low"
                            ]
                        }
                    },
                    "required": [
                        "name",
                        "description",
                        "importance"
                    ],
                    "additionalProperties": False
                }
            },
            "recommended_question_count": {
                "type": "integer",
                "minimum": 5,
                "maximum": 20
            }
        },
        "required": [
            "subject",
            "summary",
            "main_topics",
            "knowledge_units",
            "recommended_question_count"
        ],
        "additionalProperties": False
    }

    instructions = """
你是一個教材分析系統。

你只能根據使用者提供的教材文字進行分析。

規則：
1. 不可以加入教材沒有出現的外部知識。
2. subject 使用適合學生理解的大分類。
3. Knowledge Unit 是可以被測驗與追蹤學習狀態的核心概念。
4. Knowledge Unit 不要切得過細。
5. importance 只表示此教材中的重要程度。
6. recommended_question_count 依照非重複的重要概念數量決定。
7. 如果教材不足以支持某個判斷，不要猜。
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
                "name": "document_analysis",
                "strict": True,
                "schema": schema
            }
        }
    )

    return json.loads(response.output_text)


# =========================================================
# AI 題目生成
# =========================================================

def generate_questions_with_ai(
    document_text,
    analysis,
    question_count=5,
    existing_questions=None,
):
    """
    一次批量產生指定數量的題目。
    補題時會把已通過題目的摘要告訴 AI，
    降低重複出題機率。
    """

    client = get_openai_client()

    if existing_questions is None:
        existing_questions = []

    knowledge_units = [
        unit["name"]
        for unit in analysis["knowledge_units"]
    ]

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
你是一個嚴格的教材測驗出題系統。

請產生剛好 {question_count} 題單選題。

這些題目將直接用於學生測驗，因此正確性比題目數量更重要。

【最重要規則】

1. 所有題目、答案、解釋都只能根據提供的教材。
2. 絕對不可以用外部知識補充答案。
3. 每題必須只有一個明確正確答案。
4. 每題一定要有四個不同的選項。
5. distractors 必須合理，但不能造成兩個答案都成立。
6. correct_index 使用 0、1、2、3。
7. concept 優先使用以下 Knowledge Units：

{json.dumps(knowledge_units, ensure_ascii=False)}

8. source_page 必須是教材中實際提供的 Page 編號。
9. source_quote 必須逐字摘自該頁教材。
10. source_quote 必須足以支持正確答案。
11. 不要改寫 source_quote。
12. 如果某個概念無法從教材中產生無歧義題目，就換另一個概念。
13. explanation 必須解釋為什麼正確答案成立，但不能加入教材外資訊。
14. review_points 應為 2～4 個簡短、可複習的教材重點。
15. 優先涵蓋不同 Knowledge Units，避免大量題目測同一件事。
16. 不要重複已經通過的題目，也不要只是把原題換句話說。

【已經通過、不可重複的題目】
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
                "name": "quiz_generation",
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


def generate_and_refill_quiz(
    document_text,
    analysis,
    pages,
    filename,
    target_count=5,
    max_refill_rounds=2,
):
    """
    成本控制策略：

    1. 第一次一次產生 target_count 題。
    2. 只用 Python 做驗證。
    3. 若不足，只針對缺額再批量補題。
    4. 最多補題 max_refill_rounds 輪。
    5. 還是不足就直接使用已通過題目，不無限重試。

    沒有逐題 AI 二次驗證。
    """

    accepted = []
    all_rejections = []
    generation_rounds = []

    total_rounds = (
        1
        + max_refill_rounds
    )

    for round_number in range(
        1,
        total_rounds + 1,
    ):
        missing_count = (
            target_count
            - len(accepted)
        )

        if missing_count <= 0:
            break

        request_count = (
            target_count
            if round_number == 1
            else missing_count
        )

        raw_questions = (
            generate_questions_with_ai(
                document_text,
                analysis,
                question_count=request_count,
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
                analysis["subject"],
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
                    "round": round_number,
                    "number": item["number"],
                    "reasons": item["reasons"],
                }
                for item
                in round_rejections
            ]
        )

        generation_rounds.append({
            "round": round_number,
            "requested": request_count,
            "accepted": len(
                newly_accepted
            ),
            "rejected": len(
                round_rejections
            ),
            "total_accepted": len(
                accepted
            ),
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
# 動態題數
# =========================================================

def get_target_question_count(
    analysis,
):
    """
    使用 AI 建議題數，但程式端限制：
    最少 5 題，最多 20 題。
    """

    recommended = analysis.get(
        "recommended_question_count",
        5,
    )

    try:
        recommended = int(
            recommended
        )

    except Exception:
        recommended = 5

    return max(
        5,
        min(
            20,
            recommended,
        ),
    )


# =========================================================
# 目前測驗題目
# =========================================================

def get_questions():
    questions = st.session_state.generated_questions

    if questions is None:
        return []

    return questions


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

        connected, error = test_database_connection()

        if connected:
            st.success("Database connected")

        else:
            st.error("Database connection failed")

            with st.expander("查看錯誤"):
                st.code(error)

        st.caption("Prototype v0.7")


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
    st.title("📚 把教材變成你的測驗")

    st.write(
        "上傳教材 → AI 分析 → "
        "產生有教材證據的測驗。"
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
        hashlib.sha256(file_bytes)
        .hexdigest()
    )

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

        st.session_state.document_analysis = None
        st.session_state.generated_questions = None
        st.session_state.question_generation_error = None

        st.session_state.question_generation_stats = None

    st.success(
        f"已成功上傳：{uploaded_file.name}"
    )

    try:
        page_count, pages = (
            extract_pdf_text(
                file_bytes
            )
        )

    except Exception as error:
        st.error("PDF 讀取失敗")
        st.code(str(error))
        return

    document_text = (
        build_document_text(pages)
    )

    st.session_state.document_pages = pages
    st.session_state.document_text = document_text

    total_chars = sum(
        len(page["text"])
        for page in pages
    )

    pages_with_text = sum(
        1
        for page in pages
        if page["text"]
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "PDF 頁數",
        page_count,
    )

    col2.metric(
        "可讀文字頁",
        f"{pages_with_text} / {page_count}",
    )

    col3.metric(
        "擷取字元數",
        f"{total_chars:,}",
    )

    with st.expander(
        "查看文字預覽"
    ):
        st.text_area(
            "PDF 文字",
            value=create_pdf_preview(
                pages
            ),
            height=350,
            disabled=True,
            label_visibility="collapsed",
        )

    if pages_with_text == 0:
        st.warning(
            "這份 PDF 沒有可讀取文字。"
        )
        return

    st.divider()

    if (
        st.session_state.document_analysis
        is None
    ):
        st.subheader("AI 教材分析")

        if st.button(
            "AI 分析教材",
            use_container_width=True,
        ):
            try:
                with st.spinner(
                    "正在分析教材..."
                ):
                    st.session_state.document_analysis = (
                        analyze_document_with_ai(
                            document_text
                        )
                    )

                st.rerun()

            except Exception as error:
                st.error("AI 分析失敗")
                st.code(
                    f"{type(error).__name__}: "
                    f"{str(error)}"
                )

        return

    analysis = st.session_state.document_analysis

    st.subheader("教材分析")

    st.markdown("#### 建議科目")
    st.write(analysis["subject"])

    st.markdown("#### 教材摘要")
    st.write(analysis["summary"])

    st.markdown("#### 主要內容")

    for topic in analysis["main_topics"]:
        st.markdown(f"- {topic}")

    st.markdown("#### 核心概念")

    importance_map = {
        "high": "高",
        "medium": "中",
        "low": "低",
    }

    for index, unit in enumerate(
        analysis["knowledge_units"],
        start=1,
    ):
        importance = importance_map.get(
            unit["importance"],
            unit["importance"],
        )

        with st.expander(
            f"{index}. "
            f"{unit['name']} "
            f"· 重要度 {importance}"
        ):
            st.write(
                unit["description"]
            )

    target_question_count = (
        get_target_question_count(
            analysis
        )
    )

    st.metric(
        "AI 建議測驗題數",
        target_question_count,
    )

    st.divider()

    if (
        st.session_state.generated_questions
        is None
    ):
        st.subheader("產生測驗")

        st.caption(
            f"AI 建議本份教材產生 "
            f"{target_question_count} 題。"
            "若 Python 驗證淘汰題目，"
            "只批量補足缺額，最多補 2 輪。"
        )

        if st.button(
            f"產生 {target_question_count} 題測驗",
            use_container_width=True,
        ):
            try:
                with st.spinner(
                    "正在根據教材出題、驗證並批量補足缺額..."
                ):

                    (
                        final_questions,
                        all_rejections,
                        generation_rounds,
                    ) = (
                        generate_and_refill_quiz(
                            document_text,
                            analysis,
                            pages,
                            uploaded_file.name,
                            target_count=target_question_count,
                            max_refill_rounds=2,
                        )
                    )

                st.session_state.generated_questions = (
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
                            f"第 {item['round']} 輪・"
                            f"第 {item['number']} 題："
                            f"{reasons}"
                        )

                    st.session_state.question_generation_error = (
                        "\n".join(
                            rejected_text
                        )
                    )

                else:
                    st.session_state.question_generation_error = None

                st.rerun()

            except Exception as error:
                st.error("題目生成失敗")
                st.code(
                    f"{type(error).__name__}: "
                    f"{str(error)}"
                )

        return

    generated_questions = get_questions()

    st.subheader("測驗已產生")

    st.success(
        f"最終可用題目："
        f"{len(generated_questions)} 題"
    )


    generation_stats = (
        st.session_state
        .question_generation_stats
    )

    if generation_stats:

        with st.expander(
            "查看出題 / 補題紀錄"
        ):

            for item in generation_stats:

                if item["round"] == 1:
                    round_name = "初次出題"

                else:
                    round_name = (
                        f"第 {item['round'] - 1} 輪補題"
                    )

                st.write(
                    f"**{round_name}**："
                    f"要求 {item['requested']} 題，"
                    f"本輪通過 {item['accepted']} 題，"
                    f"淘汰 {item['rejected']} 題，"
                    f"累計 {item['total_accepted']} 題"
                )

    if (
        st.session_state.question_generation_error
    ):
        st.warning(
            "部分題目未通過 Python 驗證，"
            "已自動排除。"
        )

        with st.expander(
            "查看驗證結果"
        ):
            st.text(
                st.session_state
                .question_generation_error
            )

    if not generated_questions:
        st.error(
            "這次沒有題目通過來源驗證。"
        )

        if st.button(
            "重新產生題目"
        ):
            st.session_state.generated_questions = None
            st.session_state.question_generation_error = None
            st.rerun()

        return

    with st.expander(
        "查看測驗涵蓋概念"
    ):
        for index, question in enumerate(
            generated_questions,
            start=1,
        ):
            st.write(
                f"{index}. "
                f"{question['concept']}"
            )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "重新產生題目",
            use_container_width=True,
        ):
            st.session_state.generated_questions = None
            st.session_state.question_generation_error = None
            st.rerun()

    with col2:
        if st.button(
            "開始測驗",
            use_container_width=True,
        ):
            reset_quiz_state()

            st.session_state.page = "quiz"
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

    st.divider()
    st.subheader("答題結果")

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

        elif user_answer is not None:
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

                    st.caption(
                        f"教材來源："
                        f"{item['source']}"
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

show_sidebar()

if st.session_state.page == "home":
    show_home()

elif st.session_state.page == "quiz":
    show_quiz()

elif st.session_state.page == "result":
    show_result()

elif st.session_state.page == "mistakes":
    show_mistake_bank()
