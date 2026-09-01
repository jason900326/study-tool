import base64
import hashlib
import html
import json
import random
import re
import time
from io import BytesIO
from pathlib import Path
from datetime import datetime, timezone

import streamlit as st
from openai import OpenAI
from pypdf import PdfReader
from supabase import create_client


st.set_page_config(
    page_title="MedSlime",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

QUIZ_SIZE = 10

_SUPERSCRIPT_MAP = str.maketrans("+-0123456789", "⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def _to_superscript(value):
    return str(value).replace("−", "-").translate(_SUPERSCRIPT_MAP)


def normalize_scientific_notation(value):
    text_value = str(value or "")
    text_value = text_value.replace("\\times", "×").replace("\\cdot", "·")
    text_value = text_value.replace("\\(", "").replace("\\)", "")
    text_value = re.sub(
        r"(?i)\b([+-]?\d+(?:\.\d+)?)\s*[eE]([+\-−]?\d+)\b",
        lambda m: f"{m.group(1)} × 10{_to_superscript(m.group(2))}",
        text_value,
    )
    text_value = re.sub(
        r"10\s*\^\s*\{?\s*([+\-−]?\d+)\s*\}?",
        lambda m: "10" + _to_superscript(m.group(1)),
        text_value,
    )
    text_value = re.sub(r"\$([^$]*(?:10[⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹]|×\s*10)[^$]*)\$", r"\1", text_value)
    return text_value


DEFAULT_STATE = {
    "medslime_page": "home",
    "menu_open": False,
    "player_level": 4,
    "player_exp": 72,
    "coins": 520,
    "tickets": 0,
    "streak": 3,
    "slime_name": "Medi",
    "selected_slime": "青蘋果史萊姆",
    "collection": ["青蘋果史萊姆"],
    "unlocked_achievements": ["first_steps", "three_day_streak"],
    "last_gacha": None,
    "uploaded_learning_file": None,
    "material_file_hash": None,
    "material_subject": None,
    "material_questions": None,
    "material_generation_error": None,
    "material_pending_bytes": None,
    "material_pending_name": None,
    "material_pending_hash": None,
    "quiz_index": 0,
    "quiz_answers": {},
    "quiz_uncertain": {},
    "quiz_finished": False,
    "quiz_finish_pending": False,
    "national_exam_year": 2026,
    "national_exam_questions": None,
    "national_exam_meta": None,
    "national_exam_index": 0,
    "national_exam_answers": {},
    "national_exam_uncertain": {},
    "national_exam_excluded": [],
    "national_exam_total": 0,
    "national_exam_load_error": None,
    "national_exam_pending_choice": None,
    "national_exam_picker_version": 0,
    "material_mistakes_saved": False,
    "national_exam_mistakes_saved": False,
    "mistake_filter": "全部",
    "mistake_subject": None,
    "focus_status": "idle",
    "focus_phase": "focus",
    "focus_total_seconds": 1500,
    "focus_remaining_seconds": 1500,
    "focus_end_at": None,
    "focus_rewarded_blocks": 0,
    "focus_session_coins": 0,
    "focus_coins_today": 0,
    "focus_seconds_today": 0,
    "focus_round": 1,
    "focus_last_duration_minutes": 30,
    "slime_collection_filter": "全部",
    "slime_progress": {"青蘋果史萊姆": {"level": 4, "exp": 72, "fragments": 0}},
    "slime_nicknames": {"青蘋果史萊姆": "Medi"},
    "slime_name_editing": False,
    "slime_dev_preview": False,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if isinstance(value, (list, dict)) else value

ACHIEVEMENTS = [
    ("first_steps", "🌱", "第一步", "完成第一次學習", "🪙 50"),
    ("three_day_streak", "🔥", "開始上癮", "連續學習 3 天", "🎫 1"),
    ("ten_correct", "🧠", "腦袋熱身完畢", "累積答對 10 題", "🪙 100"),
    ("first_review", "🔍", "抓到弱點", "完成第一次錯題訂正", "🪙 80"),
    ("level_five", "⭐", "史萊姆長大了", "史萊姆升到 Lv.5", "🎫 1"),
    ("study_30", "⏱️", "專注半小時", "累積專注學習 30 分鐘", "🪙 120"),
]

SLIME_CATALOG = [
    {"name": "青蘋果史萊姆", "emoji": "🟢", "rarity": "N", "family": "水果系列", "mark": "🍃", "theme": "apple", "gradient": "linear-gradient(145deg,#a9efad,#47c977)", "tagline": "MedSlime 的品牌夥伴，清爽又充滿活力。", "weight": 15},
    {"name": "葡萄史萊姆", "emoji": "🟣", "rarity": "N", "family": "水果系列", "mark": "●", "theme": "grape", "gradient": "linear-gradient(145deg,#d9b0f1,#8f59bd)", "tagline": "圓滾滾又有彈性，身上帶著葡萄般的光澤。", "weight": 15},
    {"name": "草莓史萊姆", "emoji": "🍓", "rarity": "N", "family": "水果系列", "mark": "✦", "theme": "strawberry", "gradient": "linear-gradient(145deg,#ffb0b8,#ed6672)", "tagline": "活潑愛笑，身體散著像草莓籽的小亮點。", "weight": 15},
    {"name": "檸檬史萊姆", "emoji": "🟡", "rarity": "N", "family": "水果系列", "mark": "🍃", "theme": "lemon", "gradient": "linear-gradient(145deg,#fff397,#ebcf42)", "tagline": "酸酸亮亮，總是一副精神很好的樣子。", "weight": 15},
    {"name": "牛奶史萊姆", "emoji": "🥛", "rarity": "R", "family": "特殊食物系列", "mark": "◌", "theme": "milk", "gradient": "linear-gradient(145deg,#fffdf5,#e9e7df)", "tagline": "像奶凍一樣柔軟，帶著溫柔的霧面光澤。", "weight": 8.34},
    {"name": "蜂蜜史萊姆", "emoji": "🍯", "rarity": "R", "family": "特殊食物系列", "mark": "⌁", "theme": "honey", "gradient": "linear-gradient(145deg,#ffe58b,#d99425)", "tagline": "琥珀色的身體慢慢流動，甜甜又黏呼呼。", "weight": 8.33},
    {"name": "咖啡史萊姆", "emoji": "☕", "rarity": "R", "family": "特殊食物系列", "mark": "☕", "theme": "coffee", "gradient": "linear-gradient(145deg,#d6a06f,#795039)", "tagline": "帶著咖啡香氣的沉穩夥伴，頭頂有奶泡般的紋路。", "weight": 8.33},
    {"name": "雲朵史萊姆", "emoji": "☁️", "rarity": "SR", "family": "自然系列", "mark": "☁", "theme": "cloud", "gradient": "linear-gradient(145deg,#ffffff,#bcdcf1)", "tagline": "輕飄飄又蓬鬆，像把一小朵雲抱在懷裡。", "weight": 5},
    {"name": "海洋史萊姆", "emoji": "🌊", "rarity": "SR", "family": "自然系列", "mark": "〰", "theme": "ocean", "gradient": "linear-gradient(145deg,#7de4e5,#367fd0)", "tagline": "透明身體裡像藏著海浪，安靜地一波一波流動。", "weight": 5},
    {"name": "晚霞史萊姆", "emoji": "🌅", "rarity": "SSR", "family": "夢幻系列", "mark": "✦", "theme": "sunset", "gradient": "linear-gradient(145deg,#ffd36a 0%,#ff8c8d 45%,#b66fe5 100%)", "tagline": "橘粉紫的天空在身體裡流動，邊緣帶著淡金光。", "weight": 2.5},
    {"name": "星空史萊姆", "emoji": "🌌", "rarity": "SSR", "family": "夢幻系列", "mark": "✧", "theme": "starry", "gradient": "linear-gradient(145deg,#5050a5 0%,#242655 55%,#10172e 100%)", "tagline": "深色身體裡閃著星點，像裝著一小片夜空。", "weight": 2.5},
]

SLIME_BY_NAME = {item["name"]: item for item in SLIME_CATALOG}
GACHA_POOL = SLIME_CATALOG


# =========================================================
# PDF / AI
# =========================================================

@st.cache_resource
def get_openai_client():
    api_key = str(st.secrets["OPENAI_API_KEY"]).strip()
    api_key = api_key.replace("\ufeff", "").replace("\u200b", "")
    return OpenAI(api_key=api_key)


def extract_pdf_text(file_bytes):
    reader = PdfReader(BytesIO(file_bytes))
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = (page.extract_text() or "").strip()
        except Exception:
            text = ""
        if text:
            pages.append({"page": page_number, "text": text})
    return len(reader.pages), pages


def build_document_text(pages):
    return "\n\n".join(
        f"[Page {item['page']}]\n{item['text']}"
        for item in pages
        if item.get("text")
    )


def generate_material_quiz(document_text):
    client = get_openai_client()

    schema = {
        "type": "object",
        "properties": {
            "subject": {"type": "string"},
            "questions": {
                "type": "array",
                "minItems": QUIZ_SIZE,
                "maxItems": QUIZ_SIZE,
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "options": {
                            "type": "array",
                            "minItems": 4,
                            "maxItems": 4,
                            "items": {"type": "string"},
                        },
                        "correct_index": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 3,
                        },
                        "concept": {"type": "string"},
                        "explanation": {"type": "string"},
                        "review_points": {
                            "type": "array",
                            "minItems": 2,
                            "maxItems": 4,
                            "items": {"type": "string"},
                        },
                        "source_page": {"type": "integer", "minimum": 1},
                        "source_quote": {"type": "string"},
                    },
                    "required": [
                        "question",
                        "options",
                        "correct_index",
                        "concept",
                        "explanation",
                        "review_points",
                        "source_page",
                        "source_quote",
                    ],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["subject", "questions"],
        "additionalProperties": False,
    }

    instructions = f"""
你是 MedSlime 的教材出題 AI。

使用者上傳一份教材後，你要直接根據教材生成剛好 {QUIZ_SIZE} 題單選題。
使用者不需要先看摘要；題目生成完成後會立刻開始作答。

【內容限制】
1. 所有題目、選項、答案、解析與複習重點都只能根據提供的教材。
2. 不得使用教材以外的知識補充答案。
3. 每題只能有一個明確正確答案。
4. 每題固定四個不同選項。
5. {QUIZ_SIZE} 題盡量涵蓋不同概念，不要只換句話重複考同一件事。
6. 若某個概念無法做成無歧義單選題，換另一個概念。

【語言與專有名詞】
1. 一般敘述使用自然、完整、流暢的繁體中文。
2. 教材中的真正專有名詞保留教材原文，不翻譯、不漢化。
3. 例如教材寫 Beta-lactam，就保留 Beta-lactam，不可改成 Beta-內醯胺或 β-內醯胺。
4. drug names、drug classes、菌名、genes、proteins、enzymes、receptors、biomarkers、laboratory tests、pathways、molecular names、abbreviations 等優先保留原文。
5. 一般英文敘述不是專有名詞時，應改寫成自然繁體中文。
6. 不要把英文片段拼成生硬的中英混合句。
7. 四個選項應使用一致的語法層級。
8. 科學記號請使用一般文字與 Unicode 上標，例如 1 × 10⁶、3.2 × 10⁻⁴；不要輸出 LaTeX、$...$ 或 10^6。

【每題資料】
- question：完整題幹。
- options：四個選項。
- correct_index：0、1、2、3。
- concept：本題真正測驗的核心概念。
- explanation：只依教材解釋為什麼正確答案成立。
- review_points：2～4 個短而有用的複習點。
- source_page：教材實際頁碼。
- source_quote：逐字摘自該頁、足以支持正確答案的教材原文，不得改寫。

不要輸出長篇教材摘要，只需要辨識 subject 並生成 {QUIZ_SIZE} 題。
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        instructions=instructions,
        input="以下是使用者上傳教材：\n\n" + document_text,
        text={
            "format": {
                "type": "json_schema",
                "name": "medslime_material_quiz",
                "strict": True,
                "schema": schema,
            }
        },
    )

    payload = json.loads(response.output_text)
    questions = payload.get("questions", [])

    if len(questions) != QUIZ_SIZE:
        raise ValueError(f"AI 回傳題數不是 {QUIZ_SIZE} 題。")

    for idx, question in enumerate(questions, start=1):
        options = question.get("options", [])
        correct_index = question.get("correct_index")
        if len(options) != 4:
            raise ValueError(f"第 {idx} 題選項數不是 4。")
        if correct_index not in (0, 1, 2, 3):
            raise ValueError(f"第 {idx} 題答案索引不合法。")
        if len(set(options)) != 4:
            raise ValueError(f"第 {idx} 題存在重複選項。")

    return payload


def clear_quiz_answers():
    st.session_state.quiz_index = 0
    st.session_state.quiz_answers = {}
    st.session_state.quiz_uncertain = {}
    st.session_state.quiz_finished = False
    st.session_state.quiz_finish_pending = False
    st.session_state.material_mistakes_saved = False
    for i in range(QUIZ_SIZE):
        st.session_state.pop(f"material_answer_{i}", None)
        st.session_state.pop(f"material_uncertain_{i}", None)


def prepare_material_upload():
    clear_quiz_answers()
    st.session_state.material_generation_error = None
    st.session_state.pop("medslime_material_pdf", None)


# =========================================================
# National exam adapter (keeps old database structure isolated)
# =========================================================

NATIONAL_EXAM_YEARS = list(range(2026, 2016, -1))
NATIONAL_EXAM_ROUNDS = ["第一次", "第二次"]


@st.cache_resource
def get_supabase():
    url = str(st.secrets["SUPABASE_URL"]).strip().replace("\ufeff", "").replace("\u200b", "")
    key = str(st.secrets["SUPABASE_KEY"]).strip().replace("\ufeff", "").replace("\u200b", "")
    return create_client(url, key)


def roc_year_label(year):
    return f"{int(year) - 1911} 年"


_REVIEWED_PREFIX = "reviewed|"


def _mistake_is_reviewed(row):
    return str(row.get("label") or "").startswith(_REVIEWED_PREFIX)


def _parse_mistake_time(value):
    raw = str(value or "").strip()
    if not raw:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


def _mistake_attempt_identity(row):
    created = _parse_mistake_time(row.get("created_at"))
    minute_bucket = created.replace(second=0, microsecond=0)
    source_type = row.get("source_type") or "ai_document"
    if source_type == "national_exam":
        identity = (
            str(row.get("exam_year") or ""),
            str(row.get("exam_round") or ""),
            str(row.get("subject") or ""),
        )
    else:
        source = str(row.get("source") or "")
        source_base = source.split(" · Page", 1)[0].split(" · Q", 1)[0]
        identity = (source_base, str(row.get("subject") or ""))
    return minute_bucket, source_type, identity


def _mistake_question_order(row):
    number = row.get("official_question_number")
    try:
        if number is not None:
            return int(number)
    except Exception:
        pass
    try:
        return int(row.get("id") or 10**9)
    except Exception:
        return 10**9


def _sort_mistake_rows(rows):
    groups = {}
    for row in rows:
        groups.setdefault(_mistake_attempt_identity(row), []).append(row)

    grouped_rows = list(groups.values())
    grouped_rows.sort(
        key=lambda items: max(_parse_mistake_time(item.get("created_at")) for item in items),
        reverse=True,
    )

    ordered = []
    for items in grouped_rows:
        ordered.extend(sorted(items, key=_mistake_question_order))
    return ordered


def load_mistake_bank():
    response = (
        get_supabase()
        .table("mistakes")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def mark_mistake_reviewed(record_id):
    reviewed_at = datetime.now(timezone.utc).isoformat()
    (
        get_supabase()
        .table("mistakes")
        .update({"label": f"{_REVIEWED_PREFIX}{reviewed_at}"})
        .eq("id", record_id)
        .execute()
    )


def _save_mistake_rows(questions, answers, uncertain_map, source_type, meta=None, filename=None):
    meta = meta or {}
    rows = []

    for index, question in enumerate(questions):
        options = list(question.get("options") or [])
        correct_index = question.get("correct_index")
        answer_index = answers.get(index)
        uncertain = bool(uncertain_map.get(index, False))

        if answer_index is None and not uncertain:
            continue
        if correct_index not in (0, 1, 2, 3) or len(options) != 4:
            continue

        is_correct = answer_index == correct_index
        if is_correct and not uncertain:
            continue

        user_answer = options[answer_index] if answer_index in (0, 1, 2, 3) else None
        correct_answer = options[correct_index]
        subject = question.get("subject") or meta.get("subject") or st.session_state.material_subject or "未分類"

        if source_type == "national_exam":
            official_number = question.get("official_question_number", index + 1)
            source = (
                f"考選部 · {roc_year_label(meta.get('exam_year', 2026))} · "
                f"{meta.get('exam_round', '')} · {subject} · 官方第 {official_number} 題"
            )
            exam_year = meta.get("exam_year")
            exam_round = meta.get("exam_round")
            source_url = question.get("source_url")
        else:
            official_number = index + 1
            page_number = question.get("source_page")
            source = f"教材 · {filename or '上傳教材'}"
            if page_number:
                source += f" · Page {page_number}"
            source += f" · Q{index + 1}"
            exam_year = None
            exam_round = None
            source_url = None

        rows.append({
            "subject": subject,
            "concept": question.get("concept") or "未分類",
            "question": question.get("question") or "",
            "options": options,
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "uncertain": uncertain,
            "is_correct": is_correct,
            "label": "pending",
            "source": source,
            "explanation": question.get("explanation") or "",
            "review_points": question.get("review_points") or [],
            "source_quote": question.get("source_quote") or "",
            "source_type": source_type,
            "exam_year": exam_year,
            "exam_round": exam_round,
            "official_question_number": official_number,
            "source_url": source_url,
        })

    if rows:
        get_supabase().table("mistakes").insert(rows).execute()


def save_material_mistakes_if_needed():
    if st.session_state.material_mistakes_saved:
        return
    _save_mistake_rows(
        st.session_state.material_questions or [],
        st.session_state.quiz_answers,
        st.session_state.quiz_uncertain,
        "ai_document",
        filename=st.session_state.uploaded_learning_file,
    )
    st.session_state.material_mistakes_saved = True


def save_national_exam_mistakes_if_needed():
    if st.session_state.national_exam_mistakes_saved:
        return
    _save_mistake_rows(
        st.session_state.national_exam_questions or [],
        st.session_state.national_exam_answers,
        st.session_state.national_exam_uncertain,
        "national_exam",
        meta=st.session_state.national_exam_meta or {},
    )
    st.session_state.national_exam_mistakes_saved = True


@st.cache_data(ttl=1800, show_spinner=False)
def load_national_exam_subject_entries(exam_year):
    """Return subject+round entries while hiding round as a separate navigation step."""
    supabase = get_supabase()
    entries = []
    for exam_round in NATIONAL_EXAM_ROUNDS:
        response = (
            supabase
            .table("national_exam_questions")
            .select("subject")
            .eq("exam_year", exam_year)
            .eq("exam_round", exam_round)
            .limit(1000)
            .execute()
        )
        subjects = sorted({
            row.get("subject")
            for row in (response.data or [])
            if row.get("subject")
        })
        entries.extend({"subject": subject, "exam_round": exam_round} for subject in subjects)
    return sorted(entries, key=lambda item: (item["subject"], item["exam_round"]))


def load_national_exam_paper(exam_year, exam_round, subject):
    """Adapter copied from the stable study-tool logic, normalized to correct_index."""
    supabase = get_supabase()
    response = (
        supabase
        .table("national_exam_questions")
        .select(
            "id, exam_year, exam_round, subject, question_number, question, options, "
            "correct_answers, source_page_url, question_pdf_url, has_image_hint, parse_status"
        )
        .eq("exam_year", exam_year)
        .eq("exam_round", exam_round)
        .eq("subject", subject)
        .order("question_number")
        .limit(100)
        .execute()
    )
    rows = response.data or []
    answer_map = {"A": 0, "B": 1, "C": 2, "D": 3}
    usable, excluded = [], []

    for row in rows:
        options = row.get("options") or []
        correct_answers = row.get("correct_answers") or []
        reason = None
        if row.get("parse_status") != "ok":
            reason = "解析異常"
        elif row.get("has_image_hint"):
            reason = "需要圖片"
        elif len(options) != 4:
            reason = "選項不完整"
        elif len(correct_answers) != 1 or correct_answers[0] not in answer_map:
            reason = "多答案或答案格式特殊"

        if reason:
            excluded.append({"question_number": row.get("question_number"), "reason": reason})
            continue

        number = row.get("question_number")
        usable.append({
            "question": row.get("question") or "",
            "options": options,
            "correct_index": answer_map[correct_answers[0]],
            "subject": subject,
            "concept": "歷屆國考真題",
            "explanation": "",
            "review_points": [],
            "source_url": row.get("question_pdf_url") or row.get("source_page_url"),
            "official_question_number": number,
            "national_exam_id": row.get("id"),
        })

    return usable, excluded, len(rows)


def clear_national_exam_answers():
    st.session_state.national_exam_index = 0
    st.session_state.national_exam_answers = {}
    st.session_state.national_exam_uncertain = {}
    st.session_state.national_exam_mistakes_saved = False
    for i in range(100):
        st.session_state.pop(f"exam_answer_{i}", None)
        st.session_state.pop(f"exam_uncertain_{i}", None)


def start_national_exam_quiz(questions, exam_year, exam_round, subject, excluded, total):
    st.session_state.national_exam_questions = [dict(item) for item in questions]
    st.session_state.national_exam_meta = {
        "exam_year": exam_year,
        "exam_round": exam_round,
        "subject": subject,
    }
    st.session_state.national_exam_excluded = excluded
    st.session_state.national_exam_total = total
    st.session_state.national_exam_pending_choice = None
    st.session_state.national_exam_picker_version += 1
    clear_national_exam_answers()
    st.session_state.medslime_page = "national_exam_quiz"
    st.session_state.menu_open = False
    st.rerun()


# =========================================================
# Style
# =========================================================

st.markdown(
    """
    <style>
    :root { --ink:#153b2b; --green:#31c978; --line:#dbe9e1; }
    .stApp {
        background:
            radial-gradient(circle at 8% 3%, rgba(130,239,173,.18), transparent 24%),
            radial-gradient(circle at 93% 13%, rgba(118,220,255,.15), transparent 23%),
            #f8fcf9;
    }
    .block-container { max-width:1180px; padding-top:3.75rem; padding-bottom:4.5rem; }
    h1,h2,h3,p,div,button,label { font-family:"Noto Sans TC","Microsoft JhengHei",sans-serif; }

    .currency { min-height:48px; display:flex; align-items:center; justify-content:flex-end; gap:.42rem; white-space:nowrap; }
    .pill { display:inline-flex; align-items:center; min-height:38px; background:rgba(255,255,255,.92); border:1px solid #dfece4; border-radius:999px; padding:.38rem .68rem; font-weight:850; color:#244c39; box-shadow:0 6px 18px rgba(31,83,53,.045); }
    .eyebrow { color:#2ba962; font-weight:950; font-size:.86rem; letter-spacing:.04em; text-transform:uppercase; }
    .hero-title { font-size:2.25rem; line-height:1.12; font-weight:950; color:#143629; letter-spacing:-.045em; }
    .hero-copy { color:#637f70; margin-top:.6rem; line-height:1.72; }
    .section-title { font-size:1.34rem; font-weight:950; color:#173b2b; margin:1.7rem 0 .85rem; }
    .muted { color:#71887b; font-size:.92rem; }
    .card-title { color:#1d4533; font-weight:900; font-size:1.08rem; }

    [class*="st-key-topbar_shell"] [data-testid="stHorizontalBlock"] { flex-wrap:nowrap !important; align-items:center !important; gap:.35rem !important; }
    [class*="st-key-topbar_shell"] [data-testid="stHorizontalBlock"] > div:nth-child(1) { min-width:145px !important; flex:1 1 auto !important; }
    [class*="st-key-topbar_shell"] [data-testid="stHorizontalBlock"] > div:nth-child(2) { min-width:0 !important; flex:0 1 auto !important; margin-left:auto !important; }
    [class*="st-key-brand_home_"] button { background:transparent !important; border:none !important; box-shadow:none !important; padding:0 !important; min-height:48px !important; justify-content:flex-start !important; color:#17372a !important; font-size:1.55rem !important; font-weight:950 !important; letter-spacing:-.035em !important; }
    [class*="st-key-brand_home_"] button:hover,
    [class*="st-key-brand_home_"] button:active,
    [class*="st-key-brand_home_"] button:focus { background:transparent !important; border:none !important; box-shadow:none !important; transform:none !important; color:#17372a !important; }
    [class*="st-key-brand_home_"] button p { margin:0 !important; font-size:1.55rem !important; font-weight:950 !important; white-space:nowrap !important; line-height:48px !important; }

    [class*="st-key-nav_drawer"] { position:fixed !important; top:0 !important; left:0 !important; width:300px !important; max-width:84vw !important; height:100vh !important; z-index:100000 !important; overflow-y:auto !important; padding:1.1rem 1rem !important; background:rgba(248,252,249,.99) !important; border-right:1px solid #d7e7dd !important; box-shadow:16px 0 45px rgba(25,73,47,.16) !important; animation:drawerIn .18s ease-out both; }
    [class*="st-key-nav_drawer"] div.stButton > button { min-height:50px !important; border-radius:15px !important; justify-content:flex-start !important; padding-left:1rem !important; }
    [class*="st-key-drawer_close"] button { width:40px !important; height:40px !important; min-width:40px !important; min-height:40px !important; padding:0 !important; border-radius:11px !important; }
    .drawer-title { font-size:1.5rem; font-weight:950; letter-spacing:-.035em; color:#17372a; margin:.25rem 0 .15rem; }
    .drawer-note { color:#789083; font-size:.82rem; margin-bottom:1rem; }

    .home-copy-card { background:linear-gradient(135deg,#e6f9ed 0%,#f5fcf7 57%,#e9f8fd 100%); border:1px solid #d6eadd; border-radius:30px; padding:2rem; box-shadow:0 18px 44px rgba(40,106,69,.09); min-height:235px; }
    .home-slime-card { background:rgba(255,255,255,.48); border:1px solid rgba(214,234,221,.8); border-radius:30px; padding:1.45rem; min-height:235px; display:flex; flex-direction:column; align-items:center; justify-content:center; }
    .home-slime-label { font-weight:950; color:#214934; margin-top:.1rem; text-align:center; }
    .home-xp { width:82%; max-width:300px; height:9px; border-radius:999px; overflow:hidden; background:#dce9df; margin:.55rem auto .25rem; }
    .home-xp-fill { height:100%; background:linear-gradient(90deg,#58d28a,#42bda4); }
    .home-task { background:rgba(255,255,255,.95); border:1px solid #dfebe4; border-radius:23px; padding:1.2rem 1.25rem; box-shadow:0 10px 26px rgba(31,83,53,.05); min-height:145px; }
    .task-icon { width:44px; height:44px; border-radius:14px; display:flex; align-items:center; justify-content:center; background:#eefaf2; font-size:1.45rem; margin-bottom:.7rem; }
    .task-reward { margin-top:.7rem; font-weight:900; color:#2a9d5e; }

    .choice-card { background:rgba(255,255,255,.96); border:1px solid #dceae2; border-radius:25px; padding:1.45rem 1.5rem; height:196px; box-sizing:border-box; box-shadow:0 12px 28px rgba(30,78,50,.055); display:flex; flex-direction:column; }
    .choice-icon-shell { width:50px; height:50px; min-height:50px; border-radius:15px; display:flex; align-items:center; justify-content:center; background:linear-gradient(145deg,#e8f9ee,#f1fbf5); border:1px solid #d7eadf; margin-bottom:.9rem; }
    .choice-icon { font-size:1.72rem; }
    .choice-title { font-size:1.17rem; font-weight:950; color:#173b2b; }
    .choice-copy { color:#70877a; line-height:1.55; margin-top:.42rem; }
    [class*="st-key-study_choice_"] { margin-bottom:1.55rem; }
    [class*="st-key-study_choice_"] > div { height:100%; }
    [class*="st-key-study_choice_"] [data-testid="stButton"] { margin-top:.55rem; }
    .study-page-transition-anchor { height:0; overflow:hidden; }
    .block-container:has(.study-page-transition-anchor) { animation:studyPageIn .22s ease-out both; }
    .block-container:has(.study-page-transition-anchor) [class*="st-key-study_choice_"] { animation:none !important; }
    .block-container:has(.study-page-transition-anchor):has([class*="st-key-go_"] button:active) { opacity:.72; transform:translateY(2px); transition:opacity .10s ease,transform .10s ease; }
    .study-header { margin:.35rem 0 1.2rem; }
    .intro-panel { max-width:840px; margin:.3rem auto 1.15rem; background:rgba(255,255,255,.76); border:1px solid #dfebe4; border-radius:30px; padding:2rem 2rem 1.75rem; box-shadow:0 16px 38px rgba(30,82,51,.055); text-align:center; }
    .intro-art { position:relative; width:230px; height:150px; margin:0 auto .65rem; }
    .mini-slime { position:absolute; left:42px; top:35px; width:105px; height:82px; border-radius:50% 50% 40% 40%/62% 62% 38% 38%; background:linear-gradient(145deg,#9bedad,#48c878); }
    .mini-slime:before,.mini-slime:after { content:""; position:absolute; top:34px; width:8px; height:12px; background:#153c2b; border-radius:50%; }
    .mini-slime:before { left:30px; }
    .mini-slime:after { right:30px; }
    .mini-mouth { position:absolute; width:23px; height:9px; border-bottom:3px solid #153c2b; border-radius:0 0 50% 50%; left:41px; top:50px; }
    .mini-shine { position:absolute; width:22px; height:10px; background:rgba(255,255,255,.52); border-radius:50%; left:20px; top:16px; transform:rotate(-24deg); }
    .book-stack { position:absolute; right:34px; top:34px; font-size:3.6rem; }

    [data-testid="stFileUploaderDropzone"] { background:#fbfefc !important; border:1.5px dashed #bcdcc8 !important; border-radius:20px !important; padding:1.6rem !important; }
    [data-testid="stFileUploaderDropzone"] button { background:#2fc675 !important; color:white !important; border-color:#2fc675 !important; }

    .digest-card { max-width:620px; margin:1rem auto; padding:2rem 1.25rem; border:1px solid #dcebe2; border-radius:28px; background:rgba(255,255,255,.94); text-align:center; box-shadow:0 15px 34px rgba(31,83,53,.06); animation:pageIn .22s ease-out both; }
    .digest-slime { width:84px; height:68px; margin:0 auto 1rem; border-radius:50% 50% 40% 40%/62% 62% 38% 38%; background:linear-gradient(145deg,#9bedad,#48c878); position:relative; animation:slimeBounce 1.05s ease-in-out infinite; }
    .digest-slime:before,.digest-slime:after { content:""; position:absolute; top:28px; width:7px; height:10px; border-radius:50%; background:#153c2b; }
    .digest-slime:before { left:23px; }
    .digest-slime:after { right:23px; }
    .digest-dots span { display:inline-block; animation:dots 1.1s infinite; font-size:1.2rem; color:#39b975; }
    .digest-dots span:nth-child(2) { animation-delay:.15s; }
    .digest-dots span:nth-child(3) { animation-delay:.3s; }

    .quiz-stage { animation:pageIn .2s ease-out both; }
    .quiz-topline { display:flex; align-items:center; margin:.8rem 0 .5rem; }
    .quiz-count { color:#2b6850; font-weight:900; }
    .slime-track {
        display:grid;
        grid-template-columns:repeat(10, minmax(22px, 38px));
        justify-content:space-between;
        align-items:center;
        gap:.35rem;
        width:100%;
        padding:.45rem .2rem 1.15rem;
    }
    .mini-progress-slime {
        width:100%;
        max-width:38px;
        aspect-ratio:1.28 / 1;
        position:relative;
        border-radius:50% 50% 42% 42% / 62% 62% 38% 38%;
        background:#e4eee8;
        border:1px solid #d3e2d9;
        transition:transform .18s ease, opacity .18s ease, box-shadow .18s ease;
    }
    .mini-progress-slime.done {
        background:linear-gradient(145deg,#8be8a8,#43c879);
        border-color:#75d998;
    }
    .mini-progress-slime.current {
        background:linear-gradient(145deg,#9af0b3,#35c878);
        border-color:#31bd70;
        transform:scale(1.14);
        box-shadow:0 0 0 4px rgba(49,201,120,.14), 0 5px 12px rgba(35,139,78,.14);
        animation:progressSlime .75s ease-out both;
    }
    .mini-progress-slime.future { opacity:.62; }
    .mini-progress-slime::before,
    .mini-progress-slime::after {
        content:"";
        position:absolute;
        top:39%;
        width:10%;
        min-width:2px;
        aspect-ratio:1 / 1.35;
        border-radius:50%;
        background:#173b2b;
    }
    .mini-progress-slime::before { left:30%; }
    .mini-progress-slime::after { right:30%; }
    .mini-progress-slime.future::before,
    .mini-progress-slime.future::after { opacity:.28; }
    .mini-progress-mouth {
        position:absolute;
        left:40%;
        top:60%;
        width:20%;
        height:8%;
        border-bottom:1.5px solid #173b2b;
        border-radius:0 0 50% 50%;
        opacity:.85;
    }
    .mini-progress-slime.future .mini-progress-mouth { opacity:.22; }
    .mini-progress-slime.uncertain { background:linear-gradient(145deg,#ffe98f,#f4c94f); border-color:#e4bb43; opacity:1; }
    .mini-progress-slime.uncertain.current { box-shadow:0 0 0 4px rgba(240,190,55,.18),0 5px 12px rgba(183,135,25,.12); }
    .exam-round-chip { width:max-content; margin:1rem auto .45rem; padding:.28rem .78rem; border-radius:999px; background:#eaf9ef; border:1px solid #cde8d7; color:#278657; font-size:.84rem; font-weight:900; letter-spacing:.03em; }
    [class*="st-key-exam_config_card"] { background:rgba(255,255,255,.92); border:1px solid #dceae2; border-radius:26px; padding:1.2rem 1.25rem 1.35rem; box-shadow:0 12px 30px rgba(31,83,53,.055); }
    [class*="st-key-exam_config_card"] [data-baseweb="select"] > div { background:#ffffff !important; color:#244c39 !important; border-color:#d8e8df !important; }
    [class*="st-key-exam_config_card"] [data-baseweb="select"] span { color:#244c39 !important; }
    [class*="st-key-national_exam_round_select"] [role="radiogroup"] { justify-content:center !important; gap:.65rem !important; }
    [class*="st-key-national_exam_round_select"] label { background:#f5faf7; border:1px solid #d8e8df; border-radius:999px; padding:.45rem .9rem; }
    [class*="st-key-national_exam_round_select"] label:has(input:checked) { background:#e8f8ee; border-color:#92d8ad; }
    .exam-progress-label { text-align:center; color:#688476; font-size:.85rem; font-weight:800; margin:.35rem 0 .15rem; }

    /* Clickable exam progress. These are our own keyed Streamlit buttons. */
    [class*="st-key-exam_group_nav"] [data-testid="stHorizontalBlock"],
    [class*="st-key-exam_small_nav"] [data-testid="stHorizontalBlock"] {
        flex-wrap:nowrap !important;
        justify-content:center !important;
        align-items:center !important;
        gap:.34rem !important;
    }
    [class*="st-key-exam_group_nav"] [data-testid="stColumn"] {
        flex:0 1 42px !important;
        width:42px !important;
        min-width:0 !important;
    }
    [class*="st-key-exam_small_nav"] [data-testid="stColumn"] {
        flex:0 1 30px !important;
        width:30px !important;
        min-width:0 !important;
    }
    [class*="st-key-exam_group_"] button,
    [class*="st-key-exam_small_"] button {
        margin:0 auto !important;
        padding:0 !important;
        position:relative !important;
        border-radius:50% 50% 42% 42% / 62% 62% 38% 38% !important;
        color:#173b2b !important;
        border:1px solid #d1e1d7 !important;
        box-shadow:none !important;
        transform:none !important;
    }
    [class*="st-key-exam_group_"] button {
        width:38px !important;
        height:30px !important;
        min-width:38px !important;
        min-height:30px !important;
        background:#e3eee7 !important;
    }
    [class*="st-key-exam_small_"] button {
        width:27px !important;
        height:21px !important;
        min-width:27px !important;
        min-height:21px !important;
        background:#e4eee8 !important;
    }
    [class*="st-key-exam_group_"] button::before,
    [class*="st-key-exam_group_"] button::after,
    [class*="st-key-exam_small_"] button::before,
    [class*="st-key-exam_small_"] button::after {
        content:"";
        position:absolute;
        top:38%;
        border-radius:50%;
        background:#173b2b;
    }
    [class*="st-key-exam_group_"] button::before,
    [class*="st-key-exam_group_"] button::after { width:4px; height:6px; }
    [class*="st-key-exam_small_"] button::before,
    [class*="st-key-exam_small_"] button::after { width:3px; height:4px; }
    [class*="st-key-exam_group_"] button::before,
    [class*="st-key-exam_small_"] button::before { left:28%; }
    [class*="st-key-exam_group_"] button::after,
    [class*="st-key-exam_small_"] button::after { right:28%; }
    [class*="st-key-exam_group_"] button p,
    [class*="st-key-exam_small_"] button p {
        position:absolute !important;
        left:50% !important;
        top:48% !important;
        transform:translateX(-50%) !important;
        margin:0 !important;
        line-height:1 !important;
        font-size:.7rem !important;
        font-weight:700 !important;
    }
    [class*="st-key-exam_small_"] button p { font-size:.55rem !important; }
    [class*="st-key-exam_group_done_"] button,
    [class*="st-key-exam_small_done_"] button {
        background:linear-gradient(145deg,#84e5a3,#43c879) !important;
        border-color:#6fd391 !important;
        opacity:1 !important;
    }
    [class*="st-key-exam_group_current_"] button,
    [class*="st-key-exam_small_current_"] button {
        background:linear-gradient(145deg,#9af0b3,#35c878) !important;
        border-color:#31bd70 !important;
        box-shadow:0 0 0 3px rgba(49,201,120,.13) !important;
    }
    [class*="st-key-exam_group_future_"] button,
    [class*="st-key-exam_small_future_"] button { opacity:.55 !important; }
    [class*="st-key-exam_group_uncertain"] button,
    [class*="st-key-exam_small_uncertain"] button {
        background:linear-gradient(145deg,#ffe98f,#f4c94f) !important;
        border-color:#e8bd40 !important;
        opacity:1 !important;
    }
    [class*="st-key-exam_group_current_uncertain"] button,
    [class*="st-key-exam_small_current_uncertain"] button {
        background:linear-gradient(145deg,#ffe98f,#f4c94f) !important;
        border-color:#d8ac2d !important;
        box-shadow:0 0 0 3px rgba(240,190,55,.18) !important;
    }
    /* Unified question-state colors: gray untouched, red uncertain only, yellow uncertain+answer, green answered. */
    [class*="st-key-exam_group_gray_"] button,[class*="st-key-exam_small_gray_"] button,
    [class*="st-key-exam_group_current_gray_"] button,[class*="st-key-exam_small_current_gray_"] button { background:#e3eee7 !important; border-color:#d1e1d7 !important; opacity:.62 !important; }
    [class*="st-key-exam_group_red_"] button,[class*="st-key-exam_small_red_"] button,
    [class*="st-key-exam_group_current_red_"] button,[class*="st-key-exam_small_current_red_"] button { background:linear-gradient(145deg,#ffaaa8,#ef6b69) !important; border-color:#e36361 !important; opacity:1 !important; }
    [class*="st-key-exam_group_yellow_"] button,[class*="st-key-exam_small_yellow_"] button,
    [class*="st-key-exam_group_current_yellow_"] button,[class*="st-key-exam_small_current_yellow_"] button { background:linear-gradient(145deg,#ffe98f,#f4c94f) !important; border-color:#e2b83d !important; opacity:1 !important; }
    [class*="st-key-exam_group_green_"] button,[class*="st-key-exam_small_green_"] button,
    [class*="st-key-exam_group_current_green_"] button,[class*="st-key-exam_small_current_green_"] button { background:linear-gradient(145deg,#84e5a3,#43c879) !important; border-color:#6fd391 !important; opacity:1 !important; }
    [class*="st-key-exam_group_current_"] button,[class*="st-key-exam_small_current_"] button { box-shadow:0 0 0 3px rgba(49,201,120,.15) !important; transform:scale(1.08) !important; }

    [class*="st-key-material_small_nav"] [data-testid="stHorizontalBlock"] { flex-wrap:nowrap !important; justify-content:center !important; align-items:center !important; gap:.35rem !important; }
    [class*="st-key-material_small_nav"] [data-testid="stColumn"] { flex:0 1 38px !important; width:38px !important; min-width:0 !important; }
    [class*="st-key-material_small_"] button { width:34px !important; height:27px !important; min-width:34px !important; min-height:27px !important; margin:0 auto !important; padding:0 !important; position:relative !important; border-radius:50% 50% 42% 42% / 62% 62% 38% 38% !important; border:1px solid #d1e1d7 !important; color:#173b2b !important; box-shadow:none !important; transform:none !important; }
    [class*="st-key-material_small_"] button::before,[class*="st-key-material_small_"] button::after { content:""; position:absolute; top:38%; width:4px; height:6px; border-radius:50%; background:#173b2b; }
    [class*="st-key-material_small_"] button::before { left:28%; }
    [class*="st-key-material_small_"] button::after { right:28%; }
    [class*="st-key-material_small_"] button p { position:absolute !important; left:50% !important; top:48% !important; transform:translateX(-50%) !important; margin:0 !important; line-height:1 !important; font-size:.6rem !important; }
    [class*="st-key-material_small_gray_"] button,[class*="st-key-material_small_current_gray_"] button { background:#e4eee8 !important; border-color:#d3e2d9 !important; opacity:.62 !important; }
    [class*="st-key-material_small_red_"] button,[class*="st-key-material_small_current_red_"] button { background:linear-gradient(145deg,#ffaaa8,#ef6b69) !important; border-color:#e36361 !important; opacity:1 !important; }
    [class*="st-key-material_small_yellow_"] button,[class*="st-key-material_small_current_yellow_"] button { background:linear-gradient(145deg,#ffe98f,#f4c94f) !important; border-color:#e2b83d !important; opacity:1 !important; }
    [class*="st-key-material_small_green_"] button,[class*="st-key-material_small_current_green_"] button { background:linear-gradient(145deg,#8be8a8,#43c879) !important; border-color:#75d998 !important; opacity:1 !important; }
    [class*="st-key-material_small_current_"] button { box-shadow:0 0 0 4px rgba(49,201,120,.14),0 5px 12px rgba(35,139,78,.12) !important; transform:scale(1.12) !important; }
    .quiz-card { background:rgba(255,255,255,.96); border:1px solid #dceae2; border-radius:27px; padding:1.55rem 1.6rem; box-shadow:0 14px 34px rgba(31,83,53,.06); animation:questionIn .22s ease-out both; margin-bottom:.8rem; }
    .quiz-question { color:#173b2b; font-size:1.22rem; line-height:1.65; font-weight:850; }
    .quiz-meta-row { display:flex; align-items:center; justify-content:space-between; gap:.75rem; flex-wrap:wrap; margin-bottom:.45rem; }
    .official-inline-link { display:inline-flex; align-items:center; justify-content:center; padding:.34rem .62rem; border-radius:10px; background:#20252d; color:#fff !important; text-decoration:none !important; font-size:.78rem; font-weight:800; line-height:1.2; white-space:nowrap; }
    .official-inline-link:hover { opacity:.88; }

    /* 明確指定測驗互動文字，避免被 Streamlit theme 吃成白色。 */
    [data-testid="stRadio"] [role="radiogroup"] { gap:.5rem; }
    [data-testid="stRadio"] label { background:rgba(255,255,255,.82); border:1px solid #e0ebe5; border-radius:14px; padding:.62rem .8rem; }
    [data-testid="stRadio"] label p,
    [data-testid="stRadio"] label span,
    [data-testid="stCheckbox"] label p,
    [data-testid="stCheckbox"] label span { color:#244c39 !important; opacity:1 !important; }
    [data-testid="stRadio"] label:has(input:checked) { border-color:#69cf94; background:#effbf4; }
    [data-testid="stCheckbox"] { margin-top:.35rem; margin-bottom:.7rem; }

    .result-card { background:rgba(255,255,255,.96); border:1px solid #dceae2; border-radius:25px; padding:1.3rem 1.4rem; margin:.8rem 0; animation:pageIn .2s ease-out both; }
    .review-options { display:grid; gap:.48rem; margin-top:.9rem; }
    .review-option { padding:.7rem .85rem; border-radius:12px; border:1px solid #e1ebe5; background:#fbfdfc; color:#244c39; line-height:1.5; }
    .review-option.correct { background:#e9f9ef; border-color:#b8e5c9; }
    .review-option.wrong { background:#fdecec; border-color:#f3c2c2; }
    .review-option-letter { display:inline-flex; width:1.55rem; height:1.55rem; align-items:center; justify-content:center; border-radius:50%; background:rgba(255,255,255,.78); margin-right:.55rem; font-weight:900; }
    [class*="st-key-material_intro_card"] { max-width:840px; margin:.3rem auto 1.15rem; background:rgba(255,255,255,.76); border:1px solid #dfebe4; border-radius:30px; padding:2rem 2rem 1.75rem; box-shadow:0 16px 38px rgba(30,82,51,.055); text-align:center; }
    [class*="st-key-material_intro_card"] .material-intro-title { font-size:2rem; line-height:1.18; }
    [class*="st-key-material_intro_uploader"] { margin-top:1.15rem; display:flex; justify-content:center; }
    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] { border:none !important; background:transparent !important; padding:0 !important; width:100% !important; display:flex !important; justify-content:center !important; }
    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzoneInstructions"],
    [class*="st-key-material_intro_uploader"] small { display:none !important; }
    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button { width:360px !important; max-width:100% !important; min-width:280px !important; min-height:48px !important; margin:0 auto !important; position:relative !important; display:flex !important; align-items:center !important; justify-content:center !important; text-align:center !important; background:#31c978 !important; color:white !important; border:1px solid #31c978 !important; border-radius:15px !important; font-size:0 !important; overflow:hidden !important; }
    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button p,
    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button span,
    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button svg { display:none !important; font-size:0 !important; }
    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button::after { content:"上傳教材開始學習"; position:absolute !important; inset:0 !important; display:flex !important; align-items:center !important; justify-content:center !important; text-align:center !important; font-size:.95rem; font-weight:850; line-height:1 !important; }
    [data-testid="stExpander"] { background:rgba(255,255,255,.92) !important; border:1px solid #dceae2 !important; border-radius:14px !important; overflow:hidden; }
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span,
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"],
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] li,
    [data-testid="stExpander"] [data-testid="stCaptionContainer"] { color:#244c39 !important; opacity:1 !important; }

    .mistake-summary { background:linear-gradient(135deg,#edf9f1,#f7fcf9); border:1px solid #dcebe2; border-radius:20px; padding:1rem 1.15rem; margin:.7rem 0 1rem; color:#315b47; }
    .mistake-summary strong { color:#22985a; font-size:1.08rem; }

    /* Mistake folders are compact list rows instead of cards. */
    [class*="st-key-mistake_folder_row_"] { border-bottom:1px solid #dfeae4; padding:.12rem 0; }
    [class*="st-key-mistake_folder_row_"] button { min-height:58px !important; justify-content:flex-start !important; text-align:left !important; padding:.72rem .9rem !important; background:transparent !important; color:#244c39 !important; border:0 !important; border-radius:12px !important; box-shadow:none !important; }
    [class*="st-key-mistake_folder_row_"] button:hover { background:#f1faf5 !important; transform:none !important; }
    [class*="st-key-mistake_folder_row_"] button p { width:100% !important; text-align:left !important; color:#244c39 !important; font-weight:800 !important; line-height:1.45 !important; white-space:normal !important; }
    [class*="st-key-mistake_folder_row_"] button > div,
    [class*="st-key-mistake_folder_row_"] button [data-testid="stMarkdownContainer"] { width:100% !important; display:flex !important; justify-content:flex-start !important; text-align:left !important; }
    [class*="st-key-mistake_folder_row_"] button span { text-align:left !important; }

    /* Keep mistake expanders light in hover/focus/open states. */
    [class*="st-key-mistake_pending_"] [data-testid="stExpander"],
    [class*="st-key-mistake_reviewed_"] [data-testid="stExpander"] { background:#fff !important; border:1px solid #dceae2 !important; }
    [class*="st-key-mistake_pending_"] [data-testid="stExpander"] summary,
    [class*="st-key-mistake_reviewed_"] [data-testid="stExpander"] summary,
    [class*="st-key-mistake_pending_"] [data-testid="stExpander"] summary:hover,
    [class*="st-key-mistake_reviewed_"] [data-testid="stExpander"] summary:hover,
    [class*="st-key-mistake_pending_"] [data-testid="stExpander"] summary:focus,
    [class*="st-key-mistake_reviewed_"] [data-testid="stExpander"] summary:focus,
    [class*="st-key-mistake_pending_"] [data-testid="stExpander"] summary:focus-visible,
    [class*="st-key-mistake_reviewed_"] [data-testid="stExpander"] summary:focus-visible { background:#f8fcfa !important; color:#244c39 !important; }
    [class*="st-key-mistake_pending_"] [data-testid="stExpander"] summary *,
    [class*="st-key-mistake_reviewed_"] [data-testid="stExpander"] summary * { color:#244c39 !important; }

    /* Official source link inside mistake review should match MedSlime, not dark theme. */
    [class*="st-key-mistake_pending_"] [data-testid="stLinkButton"] a,
    [class*="st-key-mistake_reviewed_"] [data-testid="stLinkButton"] a { background:#fff !important; color:#244c39 !important; border:1px solid #d7e7de !important; box-shadow:none !important; }
    [class*="st-key-mistake_pending_"] [data-testid="stLinkButton"] a:hover,
    [class*="st-key-mistake_reviewed_"] [data-testid="stLinkButton"] a:hover { background:#eef9f3 !important; color:#1f6f47 !important; border-color:#bfe3ce !important; }

    .mistake-row-question { color:#173b2b; font-size:1.05rem; font-weight:850; line-height:1.6; margin:.4rem 0 .8rem; }
    .mistake-status { display:inline-flex; align-items:center; border-radius:999px; padding:.2rem .55rem; font-size:.75rem; font-weight:900; margin-right:.35rem; }
    .mistake-status.wrong { background:#fdecec; color:#c84e4e; }
    .mistake-status.uncertain { background:#fff4d7; color:#ad7c14; }
    .mistake-status.reviewed { background:#e9f7ee; color:#2c8d58; }
    [class*="st-key-mistake_reviewed_"] { opacity:.7; }
    .mistake-source { color:#70877a; font-size:.84rem; line-height:1.55; margin-top:.75rem; }

    /* Pomodoro focus timer */
    [class*="st-key-focus_setup_card"], [class*="st-key-focus_timer_card"] { max-width:880px; margin:.7rem auto 1rem; background:rgba(255,255,255,.94); border:1px solid #dceae2; border-radius:28px; padding:1.4rem 1.5rem 1.5rem; box-shadow:0 16px 38px rgba(30,82,51,.055); }
    .focus-clock { text-align:center; color:#143629; font-size:5.2rem; line-height:1; font-weight:950; letter-spacing:-.055em; margin:.75rem 0 .45rem; font-variant-numeric:tabular-nums; }
    .focus-phase { text-align:center; color:#2aa665; font-size:.88rem; font-weight:950; letter-spacing:.05em; text-transform:uppercase; }
    .focus-sub { text-align:center; color:#6d8779; line-height:1.55; margin:.2rem 0 1rem; }
    .focus-path { position:relative; height:126px; margin:1.1rem .45rem .8rem; border-radius:24px; background:linear-gradient(180deg,#f8fcf9,#eff8f3); border:1px solid #dcebe2; overflow:hidden; }
    .focus-path::after { content:""; position:absolute; left:4%; right:5%; bottom:25px; height:5px; border-radius:999px; background:#dce9df; }
    .focus-path-fill { position:absolute; left:4%; bottom:25px; height:5px; max-width:91%; border-radius:999px; background:linear-gradient(90deg,#60d790,#31c978); z-index:1; transition:width .8s linear; }
    .focus-finish { position:absolute; right:3.5%; bottom:33px; font-size:1.45rem; z-index:2; }
    .focus-runner { position:absolute; bottom:34px; width:70px; height:55px; border-radius:50% 50% 40% 40%/62% 62% 38% 38%; transform:translateX(-50%); box-shadow:inset -7px -9px 0 rgba(20,70,45,.08),0 8px 15px rgba(35,118,69,.13); z-index:4; transition:left .85s linear; animation:focusHop .65s ease-in-out infinite; }
    .focus-runner.has-art { width:88px; height:72px; bottom:28px; border-radius:0; box-shadow:none; background:transparent !important; overflow:visible; }
    .focus-runner.has-art::before,.focus-runner.has-art::after { display:none; }
    .focus-runner.has-art .focus-runner-mouth { display:none; }
    .focus-runner-art { width:100%; height:100%; object-fit:contain; display:block; filter:drop-shadow(0 7px 8px rgba(35,118,69,.12)); }
    .focus-runner::before,.focus-runner::after { content:""; position:absolute; top:22px; width:6px; height:9px; border-radius:50%; background:#173b2b; }
    .focus-runner::before { left:20px; }
    .focus-runner::after { right:20px; }
    .focus-runner-mouth { position:absolute; left:27px; top:32px; width:17px; height:7px; border-bottom:2px solid #173b2b; border-radius:0 0 50% 50%; }
    .focus-runner.resting { animation:focusRest 1.5s ease-in-out infinite; }
    .focus-sleep { position:absolute; left:68%; top:-20px; font-size:1.1rem; }
    .focus-reward-note { text-align:center; color:#789083; font-size:.84rem; margin-top:.35rem; }
    .focus-earned { display:inline-flex; align-items:center; justify-content:center; padding:.3rem .7rem; border-radius:999px; background:#eef9f2; color:#238a53; font-weight:900; }
    .focus-done-card { text-align:center; padding:1rem .4rem .3rem; }
    .focus-done-title { color:#173b2b; font-size:1.55rem; font-weight:950; margin:.25rem 0; }
    @keyframes focusHop { 0%,100% { transform:translateX(-50%) translateY(0) scaleX(1.03); } 45% { transform:translateX(-50%) translateY(-10px) scaleX(.96); } 65% { transform:translateX(-50%) translateY(-5px) scaleX(1.04); } }
    @keyframes focusRest { 0%,100% { transform:translateX(-50%) translateY(0) scaleX(1.04) scaleY(.94); } 50% { transform:translateX(-50%) translateY(2px) scaleX(1.07) scaleY(.91); } }

    /* My Slime collection / catalog */
    .slime-page-header { margin:.35rem 0 1rem; }
    .slime-hub-actions { margin:.4rem 0 1rem; }
    .companion-panel { display:flex; gap:1.7rem; align-items:center; background:linear-gradient(135deg,#eefaf3,#ffffff 62%,#edf8fc); border:1px solid #d7eadf; border-radius:30px; padding:1.55rem 1.7rem; box-shadow:0 16px 38px rgba(30,82,51,.065); margin:.5rem 0 1.25rem; overflow:hidden; }
    [class*="st-key-companion_panel_live"] { background:linear-gradient(135deg,#eefaf3,#ffffff 62%,#edf8fc); border:1px solid #d7eadf; border-radius:30px; padding:1.55rem 1.7rem; box-shadow:0 16px 38px rgba(30,82,51,.065); margin:.5rem 0 1.25rem; overflow:hidden; }
    [class*="st-key-companion_panel_live"] .companion-art { width:100%; min-width:0; }
    [class*="st-key-companion_panel_live"] [data-testid="stHorizontalBlock"] { align-items:center; }
    .companion-art { width:220px; min-width:220px; display:flex; justify-content:center; align-items:center; }
    .companion-info { flex:1; min-width:0; }
    .companion-topline { display:flex; flex-wrap:wrap; gap:.45rem; align-items:center; margin-bottom:.35rem; }
    .rarity-chip,.family-chip,.owned-chip { display:inline-flex; align-items:center; min-height:27px; padding:.2rem .55rem; border-radius:999px; font-size:.76rem; font-weight:950; }
    .rarity-chip { background:#173b2b; color:#fff !important; }
    .rarity-chip.rarity-N { background:#173b2b; color:#fff !important; }
    .rarity-chip.rarity-R { background:#4d77bd; color:#fff !important; }
    .rarity-chip.rarity-SR { background:#8b63bc; color:#fff !important; }
    .rarity-chip.rarity-SSR { background:linear-gradient(90deg,#9d6bc3,#d88c61); color:#fff !important; }
    .family-chip { background:#fff; border:1px solid #dceae2; color:#627d6f; }
    .owned-chip { background:#e7f8ed; color:#228a51; }
    .companion-name { color:#173b2b; font-size:1.65rem; font-weight:950; letter-spacing:-.03em; margin:.2rem 0 .25rem; }
    [class*="st-key-slime_name_button_"] button { background:transparent !important; border:none !important; box-shadow:none !important; min-height:0 !important; height:auto !important; padding:.08rem 0 .18rem !important; justify-content:flex-start !important; color:#173b2b !important; font-size:1.65rem !important; font-weight:950 !important; letter-spacing:-.03em !important; }
    [class*="st-key-slime_name_button_"] button:hover,[class*="st-key-slime_name_button_"] button:focus,[class*="st-key-slime_name_button_"] button:active { background:transparent !important; border:none !important; box-shadow:none !important; transform:none !important; color:#1f8d56 !important; }
    [class*="st-key-slime_name_button_"] button p { font-size:1.65rem !important; font-weight:950 !important; margin:0 !important; }
    [class*="st-key-slime_nickname_editor_"] { max-width:420px; margin:.1rem 0 .5rem; }
    .achievement-card { background:white; border:1px solid #dfebe4; border-radius:22px; padding:1rem; min-height:165px; margin-bottom:1rem; box-shadow:0 8px 22px rgba(31,83,53,.035); }
    .achievement-card.locked { background:#f6f9f7; border-color:#e3ebe6; }
    .achievement-icon { font-size:2rem; margin-bottom:.25rem; }
    .achievement-card.locked .achievement-icon { filter:grayscale(1); opacity:.52; }
    .achievement-title { color:#1d4533; font-weight:900; font-size:1.08rem; }
    .achievement-card.locked .achievement-title { color:#53695d; }
    .achievement-desc { color:#71887b; margin-top:.2rem; line-height:1.45; }
    .achievement-card.locked .achievement-desc { color:#7c8f84; }
    .achievement-status { margin-top:.65rem; font-weight:850; color:#258c55; }
    .achievement-card.locked .achievement-status { color:#71857a; }
    .companion-species { color:#638071; font-size:.9rem; margin-bottom:.8rem; }
    .companion-level-row { display:flex; align-items:center; justify-content:space-between; gap:1rem; color:#285841; font-weight:900; margin:.2rem 0 .35rem; }
    .companion-xp { width:100%; height:10px; border-radius:999px; overflow:hidden; background:#dce9df; }
    .companion-xp > span { display:block; height:100%; border-radius:inherit; background:linear-gradient(90deg,#58d28a,#42bda4); }
    .companion-meta { display:flex; flex-wrap:wrap; gap:.8rem; color:#71887b; font-size:.84rem; margin-top:.65rem; }
    .catalog-summary { display:flex; justify-content:space-between; gap:1rem; align-items:end; flex-wrap:wrap; margin:1.35rem 0 .35rem; }
    .catalog-count { color:#6f8679; font-size:.88rem; font-weight:750; }
    [class*="st-key-slime_catalog_card_"] { background:rgba(255,255,255,.96); border:1px solid #dceae2; border-radius:22px; padding:1rem; min-height:350px; box-shadow:0 10px 25px rgba(31,83,53,.045); margin-bottom:.8rem; }
    [class*="st-key-slime_catalog_card_"]:has(.catalog-card-selected) { border-color:#77d69d; box-shadow:0 0 0 3px rgba(49,201,120,.1),0 12px 26px rgba(31,83,53,.05); }
    .catalog-card-selected { height:0; overflow:hidden; }
    .catalog-art-shell { min-height:145px; display:flex; align-items:center; justify-content:center; position:relative; }
    .catalog-card-head { display:flex; justify-content:space-between; gap:.4rem; align-items:center; margin-top:.35rem; }
    .catalog-card-name { color:#1c4332; font-size:1.03rem; font-weight:950; line-height:1.35; }
    .catalog-card-tagline { color:#70877a; font-size:.82rem; line-height:1.5; min-height:50px; margin:.55rem 0 .65rem; }
    .catalog-card-meta { color:#789083; font-size:.78rem; display:flex; justify-content:flex-end; gap:.5rem; border-top:1px solid #edf2ef; padding-top:.55rem; margin-top:.35rem; }
    .catalog-lock-copy { color:#84968c; font-size:.8rem; font-weight:850; }
    .catalog-mystery-copy { text-align:center; color:#687b71; font-size:.83rem; line-height:1.45; min-height:50px; margin:.55rem 0 .65rem; }
    .limited-empty { border:1px dashed #cbded2; background:linear-gradient(135deg,#fbfdfc,#f2f8f5); border-radius:24px; padding:2rem 1.3rem; text-align:center; color:#627b6d; margin:.75rem 0; }
    .limited-lock { font-size:2.2rem; margin-bottom:.45rem; }
    .art-placeholder-note { color:#8aa095; font-size:.75rem; margin-top:.45rem; }

    .catalog-slime { position:relative; border-radius:50% 50% 40% 40%/62% 62% 38% 38%; box-shadow:inset -10px -13px 0 rgba(25,70,45,.075),0 12px 22px rgba(39,110,73,.12); }
    .catalog-slime-card { width:112px; height:88px; }
    .catalog-slime-home { width:150px; height:118px; margin:0 auto .8rem; animation:slimeBounce 2.4s ease-in-out infinite; }
    .official-slime-art { display:flex; align-items:center; justify-content:center; overflow:hidden; border-radius:24px; }
    .official-slime-art img { display:block; width:100%; height:100%; object-fit:contain; border-radius:inherit; }
    .official-slime-art-card { width:154px; height:124px; margin:0 auto; }
    .official-slime-art-home { width:190px; height:153px; margin:0 auto .45rem; animation:slimeBounce 2.4s ease-in-out infinite; }
    .official-slime-art-hero { width:220px; height:177px; margin:0 auto; animation:slimeBounce 2.2s ease-in-out infinite; }
    .official-slime-art.locked { filter:saturate(.42); opacity:.64; }
    .catalog-slime-hero { width:176px; height:138px; animation:slimeBounce 2.2s ease-in-out infinite; }
    .catalog-slime::after { content:""; position:absolute; left:20%; top:14%; width:23%; height:12%; border-radius:50%; background:rgba(255,255,255,.42); transform:rotate(-22deg); }
    .catalog-eye { position:absolute; top:43%; width:8%; height:12%; border-radius:50%; background:#173b2b; z-index:3; }
    .eye-left { left:31%; } .eye-right { right:31%; }
    .catalog-mouth { position:absolute; left:41%; top:61%; width:19%; height:10%; border-bottom:3px solid #173b2b; border-radius:0 0 50% 50%; z-index:3; }
    .catalog-mark { position:absolute; left:50%; top:-18%; transform:translateX(-50%); z-index:5; font-size:1.3rem; font-weight:950; filter:drop-shadow(0 3px 4px rgba(35,70,50,.1)); }
    .catalog-slime-hero .catalog-mark { font-size:1.8rem; }
    .catalog-lock { position:absolute; right:-10px; top:-9px; width:32px; height:32px; display:flex; align-items:center; justify-content:center; border-radius:50%; background:#fff; border:1px solid #d8e5dd; box-shadow:0 4px 12px rgba(36,67,50,.12); font-size:.9rem; z-index:8; }
    .catalog-slime.locked:not(.mystery) { filter:saturate(.42); opacity:.64; box-shadow:inset -10px -13px 0 rgba(25,70,45,.06),0 8px 16px rgba(39,110,73,.07); }
    .catalog-slime.mystery { filter:saturate(.15); opacity:.78; box-shadow:0 10px 22px rgba(22,35,29,.12); }
    .catalog-slime.mystery::after { opacity:.08; }
    .catalog-slime.mystery .catalog-mark { top:34%; color:#fff; font-size:2rem; opacity:.62; }
    .theme-strawberry::before { content:"✦  ·  ✦"; position:absolute; left:19%; top:18%; color:rgba(255,235,165,.72); font-size:.55rem; letter-spacing:.38rem; transform:rotate(-8deg); }
    .theme-honey::before { content:""; position:absolute; right:9%; bottom:-8%; width:22%; height:26%; border-radius:0 0 50% 50%; background:rgba(199,126,26,.46); }
    .theme-coffee::before { content:""; position:absolute; left:29%; top:5%; width:45%; height:16%; border-radius:50%; border-top:4px solid rgba(255,239,208,.78); transform:rotate(-8deg); }
    .theme-cloud { border-radius:48% 52% 37% 43%/58% 61% 39% 42%; box-shadow:-20px 7px 0 -8px rgba(228,241,248,.95),20px 7px 0 -8px rgba(213,235,247,.95),0 12px 22px rgba(70,110,130,.1); }
    .theme-ocean::before { content:"〰"; position:absolute; left:17%; right:17%; bottom:8%; color:rgba(255,255,255,.62); font-size:2rem; text-align:center; line-height:1; }
    .theme-sunset::before,.theme-starry::before { content:"✦  ·  ✧"; position:absolute; left:16%; top:17%; color:rgba(255,255,255,.68); letter-spacing:.35rem; font-size:.8rem; }
    .theme-starry::before { content:"✦ · ✧ ·"; top:21%; color:rgba(255,235,174,.78); }

    .slime { width:178px; height:142px; margin:0 auto 1rem; border-radius:50% 50% 40% 40%/62% 62% 38% 38%; background:linear-gradient(145deg,#9bedad,#48c878); box-shadow:inset -14px -18px 0 rgba(25,130,74,.09),0 20px 30px rgba(39,139,82,.18); position:relative; }
    .slime:before,.slime:after { content:""; position:absolute; top:60px; width:13px; height:19px; background:#153c2b; border-radius:50%; }
    .slime:before { left:49px; }
    .slime:after { right:49px; }
    .mouth { position:absolute; width:35px; height:15px; border-bottom:4px solid #153c2b; border-radius:0 0 50% 50%; left:72px; top:88px; }
    .shine { position:absolute; width:32px; height:16px; background:rgba(255,255,255,.48); border-radius:50%; left:35px; top:29px; transform:rotate(-24deg); }
    .gacha-result { text-align:center; background:white; border:1px solid #dcebe2; border-radius:28px; padding:2rem; }
    .rarity-N { color:#6b7d72; font-weight:900; }
    .rarity-R { color:#3d72c8; font-weight:900; }
    .rarity-SSR { color:#b58213; font-weight:950; }

    div.stButton > button { border-radius:15px; min-height:46px; font-weight:850; transition:.15s ease; }
    div.stButton > button:hover { transform:translateY(-1px); }
    div.stButton > button[kind="primary"] { background:#31c978; color:white; border:1px solid #31c978; box-shadow:0 7px 18px rgba(49,201,120,.16); }
    div.stButton > button[kind="secondary"] { background:rgba(255,255,255,.9); color:#244c39; border:1px solid #d8e8df; }
    div.stButton > button:disabled { background:#f2f6f3 !important; color:#9aac9f !important; border-color:#e2ebe5 !important; }

    .home-copy-card,.home-slime-card,.home-task,.intro-panel { animation:pageIn .20s ease-out both; }
    @keyframes drawerIn { from { transform:translateX(-18px); opacity:0; } to { transform:translateX(0); opacity:1; } }
    @keyframes pageIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
    @keyframes studyPageIn { from { opacity:0; transform:translateY(5px); } to { opacity:1; transform:translateY(0); } }
    @keyframes questionIn { from { opacity:0; transform:translateX(9px); } to { opacity:1; transform:translateX(0); } }
    @keyframes slimeBounce { 0%,100% { transform:translateY(0) scaleX(1); } 45% { transform:translateY(-8px) scaleX(.97); } 60% { transform:translateY(-5px) scaleX(1.03); } }
    @keyframes dots { 0%,70%,100% { opacity:.28; transform:translateY(0); } 35% { opacity:1; transform:translateY(-3px); } }
    @keyframes progressSlime { 0% { transform:scale(.94); } 65% { transform:scale(1.19); } 100% { transform:scale(1.14); } }

    @media (max-width:700px) {
        .block-container { padding-left:.85rem; padding-right:.85rem; padding-bottom:3rem; }
        [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button { width:100% !important; max-width:100% !important; min-width:0 !important; }
        [class*="st-key-material_intro_card"] { padding:1.45rem 1.05rem 1.3rem !important; border-radius:24px !important; }
        [class*="st-key-material_intro_card"] .material-intro-title { font-size:1.42rem !important; line-height:1.28 !important; letter-spacing:-.025em !important; max-width:100% !important; overflow-wrap:normal !important; word-break:keep-all !important; }
        [class*="st-key-material_intro_card"] .hero-copy { font-size:.92rem !important; line-height:1.65 !important; }
        [class*="st-key-material_intro_card"] .intro-art { transform:scale(.88); transform-origin:center bottom; margin-bottom:-.1rem; }
        .hero-title { font-size:1.9rem; }
        .focus-clock { font-size:3.8rem; }
        .focus-path { height:108px; margin-left:0; margin-right:0; }
        .focus-runner { width:60px; height:47px; }
        .focus-runner.has-art { width:76px; height:62px; bottom:27px; }
        .focus-runner::before,.focus-runner::after { top:19px; width:5px; height:8px; }
        .focus-runner::before { left:17px; }
        .focus-runner::after { right:17px; }
        .focus-runner-mouth { left:23px; top:28px; width:15px; }
        .home-copy-card,.home-slime-card { min-height:auto; }
        .choice-card { height:178px; min-height:178px; padding:1.2rem; }
        [class*="st-key-study_choices_grid"] [data-testid="stHorizontalBlock"] { gap:.85rem !important; }
        [class*="st-key-study_choices_grid"] [data-testid="stColumn"] { margin-bottom:0 !important; }
        [class*="st-key-study_choice_"] { margin-bottom:0 !important; }
        [class*="st-key-study_choice_"] [data-testid="stButton"] { margin-top:.55rem !important; margin-bottom:0 !important; }
        .intro-panel { padding:1.45rem 1.1rem; }
        .quiz-card { padding:1.2rem 1.1rem; }
        .quiz-question { font-size:1.08rem; }
        .slime-track { grid-template-columns:repeat(10, minmax(19px, 30px)); gap:.22rem; padding:.4rem 0 1rem; }
        [class*="st-key-exam_group_nav"] [data-testid="stHorizontalBlock"],
        [class*="st-key-exam_small_nav"] [data-testid="stHorizontalBlock"] { gap:.14rem !important; }
        [class*="st-key-exam_group_nav"] [data-testid="stColumn"] { flex-basis:28px !important; width:28px !important; }
        [class*="st-key-exam_small_nav"] [data-testid="stColumn"] { flex-basis:23px !important; width:23px !important; }
        [class*="st-key-exam_group_"] button { width:27px !important; height:21px !important; min-width:27px !important; min-height:21px !important; }
        [class*="st-key-exam_small_"] button { width:21px !important; height:17px !important; min-width:21px !important; min-height:17px !important; }
        [class*="st-key-exam_group_"] button::before,[class*="st-key-exam_group_"] button::after { width:3px; height:4px; }
        [class*="st-key-exam_small_"] button::before,[class*="st-key-exam_small_"] button::after { width:2px; height:3px; }
        [class*="st-key-exam_group_"] button p { font-size:.52rem !important; }
        [class*="st-key-exam_small_"] button p { font-size:.42rem !important; }
        [class*="st-key-material_small_nav"] [data-testid="stHorizontalBlock"] { gap:.16rem !important; }
        [class*="st-key-material_small_nav"] [data-testid="stColumn"] { flex-basis:25px !important; width:25px !important; }
        [class*="st-key-material_small_"] button { width:23px !important; height:18px !important; min-width:23px !important; min-height:18px !important; }
        [class*="st-key-material_small_"] button::before,[class*="st-key-material_small_"] button::after { width:2px; height:3px; }
        [class*="st-key-material_small_"] button p { font-size:.42rem !important; }
        [class*="st-key-topbar_shell"] [data-testid="stHorizontalBlock"] { gap:.18rem !important; }
        [class*="st-key-topbar_shell"] [data-testid="stHorizontalBlock"] > div:nth-child(1) { min-width:118px !important; }
        [class*="st-key-topbar_shell"] [data-testid="stHorizontalBlock"] > div:nth-child(2) { min-width:0 !important; }
        [class*="st-key-brand_home_"] button,[class*="st-key-brand_home_"] button p { min-height:42px !important; line-height:42px !important; font-size:1.25rem !important; }
        .currency { min-height:42px; gap:.15rem; }
        .pill { min-height:31px; padding:.23rem .32rem; font-size:.67rem; box-shadow:none; }
        .companion-panel { flex-direction:column; text-align:center; gap:.75rem; padding:1.25rem 1rem; }
        .companion-art { width:100%; min-width:0; }
        .companion-topline,.companion-meta { justify-content:center; }
        .companion-name { font-size:1.4rem; }
        .catalog-slime-hero { width:145px; height:114px; }
        [class*="st-key-slime_catalog_card_"] { min-height:330px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Navigation / shared visuals
# =========================================================

def goto(page):
    st.session_state.medslime_page = page
    st.session_state.menu_open = False
    st.rerun()


def set_page_without_extra_rerun(page):
    st.session_state.medslime_page = page
    st.session_state.menu_open = False


def render_back_button(label, target, key):
    st.button(
        f"← {label}",
        key=key,
        on_click=set_page_without_extra_rerun,
        args=(target,),
    )


def topbar():
    with st.container(key="topbar_shell"):
        brand_col, currency_col = st.columns([1, 2.1], vertical_alignment="center")
        with brand_col:
            if st.button("MedSlime.", key=f"brand_home_{st.session_state.medslime_page}", help="返回首頁"):
                goto("home")
        with currency_col:
            st.markdown(
                f'<div class="currency"><span class="pill">🔥 {st.session_state.streak} 天</span><span class="pill">🪙 {st.session_state.coins}</span><span class="pill">🎫 {st.session_state.tickets}</span></div>',
                unsafe_allow_html=True,
            )


def slime_markup():
    return '<div class="slime"><div class="shine"></div><div class="mouth"></div></div>'


def slime_data(name):
    return SLIME_BY_NAME.get(name, SLIME_BY_NAME["青蘋果史萊姆"])


def get_slime_progress(name):
    progress = st.session_state.slime_progress
    if name not in progress:
        progress[name] = {"level": 1, "exp": 0, "fragments": 0}
    return progress[name]


def get_slime_nickname(name):
    nicknames = st.session_state.slime_nicknames
    if name not in nicknames:
        nicknames[name] = name.replace("史萊姆", "")
    return nicknames[name]


def selected_slime_background():
    return slime_data(st.session_state.selected_slime)["gradient"]


def _local_asset_data_uri(asset_path):
    with open(asset_path, "rb") as asset_file:
        encoded = base64.b64encode(asset_file.read()).decode("ascii")
    suffix = str(asset_path).lower().rsplit(".", 1)[-1]
    mime = "image/webp" if suffix == "webp" else "image/png"
    return f"data:{mime};base64,{encoded}"


def slime_avatar_markup(item, size="card", locked=False, mystery=False, selected=False):
    if not mystery:
        asset_path = Path(f"assets/slimes/{item.get('theme')}.PNG")
        if asset_path.exists():
            locked_class = " locked" if locked else ""
            selected_class = " selected" if selected else ""
            art_uri = _local_asset_data_uri(asset_path)
            safe_alt = html.escape(item.get("name", "史萊姆"))
            return (
                f'<div class="official-slime-art official-slime-art-{size}{locked_class}{selected_class}">'
                f'<img src="{art_uri}" alt="{safe_alt}"></div>'
            )
    classes = ["catalog-slime", f"catalog-slime-{size}", f"theme-{item['theme']}"]
    if locked:
        classes.append("locked")
    if mystery:
        classes.append("mystery")
    if selected:
        classes.append("selected")
    gradient = "linear-gradient(145deg,#66706b,#252d29)" if mystery else item["gradient"]
    mark = "?" if mystery else item.get("mark", "")
    face = "" if mystery else '<span class="catalog-eye eye-left"></span><span class="catalog-eye eye-right"></span><span class="catalog-mouth"></span>'
    lock = '<span class="catalog-lock">🔒</span>' if locked else ""
    return (
        f'<div class="{" ".join(classes)}" style="background:{gradient}">'
        f'<span class="catalog-mark">{mark}</span>{face}{lock}</div>'
    )


def render_loading_card(filename):
    st.markdown(
        f'<div class="digest-card"><div class="digest-slime"></div><div class="card-title" style="font-size:1.25rem">史萊姆正在消化教材</div><div class="muted" style="margin-top:.45rem">{html.escape(str(filename))}</div><div class="hero-copy" style="margin-top:.75rem">正在讀取內容、整理概念並準備 {QUIZ_SIZE} 題測驗。</div><div class="digest-dots"><span>●</span><span>●</span><span>●</span></div></div>',
        unsafe_allow_html=True,
    )


# =========================================================
# Home / Study
# =========================================================

def home():
    topbar()
    companion_progress = get_slime_progress(st.session_state.selected_slime)
    companion_nickname = get_slime_nickname(st.session_state.selected_slime)
    left, right = st.columns([1.35, 1], gap="large", vertical_alignment="center")
    with left:
        st.markdown('<div class="home-copy-card"><div class="eyebrow">TODAY’S STUDY</div><div class="hero-title">把今天的知識<br>餵給你的史萊姆。</div><div class="hero-copy">做題、訂正與專注學習都會讓史萊姆成長。先完成一小段，再去看看今天能不能拿到新的抽卡券。</div></div>', unsafe_allow_html=True)
        if st.button("🧠 開始學習", type="primary", use_container_width=True, key="home_start_study"):
            goto("study")
        if st.button("🐾 我的史萊姆", use_container_width=True, key="home_my_slime"):
            goto("slime")
    with right:
        companion_item = slime_data(st.session_state.selected_slime)
        st.markdown('<div class="home-slime-card">' + slime_avatar_markup(companion_item, size="home") + f'<div class="home-slime-label">{html.escape(companion_nickname)} · Lv.{companion_progress["level"]}</div><div class="home-xp"><div class="home-xp-fill" style="width:{min(100, companion_progress["exp"])}%"></div></div><div class="muted">{companion_progress["exp"]} / 100 EXP · {st.session_state.selected_slime}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">今日任務</div>', unsafe_allow_html=True)
    focused_minutes = min(20, int(st.session_state.focus_seconds_today // 60))
    tasks = [
        ("🧠", "完成 5 題", "0 / 5", "+20 EXP"),
        ("🔍", "訂正 1 題", "0 / 1", "+50 🪙"),
        ("⏱️", "學習 20 分鐘", f"{focused_minutes} / 20", "+1 🎫"),
    ]
    cols = st.columns(3, gap="medium")
    for col, (icon, title, progress, reward) in zip(cols, tasks):
        with col:
            st.markdown(f'<div class="home-task"><div class="task-icon">{icon}</div><div class="card-title">{title}</div><div class="muted">{progress}</div><div class="task-reward">{reward}</div></div>', unsafe_allow_html=True)


def study_home():
    topbar()
    render_back_button("返回首頁", "home", "back_study_home")
    st.markdown('<div class="study-page-transition-anchor"></div>', unsafe_allow_html=True)
    st.markdown('<div class="study-header"><div class="eyebrow">STUDY</div><div class="hero-title" style="font-size:2.05rem">你想怎麼學習呢？</div><div class="hero-copy">選擇適合你現在狀態的方式，MedSlime 陪你一起進步。</div></div>', unsafe_allow_html=True)
    rows = [
        [("📄", "我有教材", "上傳 PDF 教材，AI 會直接生成 10 題並開始測驗。", "study_material_intro"), ("🧪", "我要刷國考", "練習歷屆國考題目，快速檢測實力與弱點。", "national_exam")],
        [("📘", "我要複習錯題", "回顧答錯或不確定的題目，加強你的弱點。", "mistakes"), ("⏱️", "我要專心讀書", "用番茄鐘陪你專注，完成每一小段就累積學習時間。", "focus_timer")],
    ]
    with st.container(key="study_choices_grid"):
        for row_index, row in enumerate(rows):
            cols = st.columns(2, gap="large")
            for col_index, (col, (icon, title, copy, target)) in enumerate(zip(cols, row)):
                with col:
                    with st.container(key=f"study_choice_{row_index}_{col_index}"):
                        st.markdown(f'<div class="choice-card"><div class="choice-icon-shell"><div class="choice-icon">{icon}</div></div><div class="choice-title">{title}</div><div class="choice-copy">{copy}</div></div>', unsafe_allow_html=True)
                        if target:
                            st.button(
                                "進入 →",
                                key=f"go_{target}",
                                use_container_width=True,
                                type="primary",
                                on_click=set_page_without_extra_rerun,
                                args=(target,),
                            )
                        else:
                            st.button("即將開放", key=f"soon_{title}", use_container_width=True, disabled=True)

    # Warm the current-year exam subject list while the Study page is already open.
    # This avoids leaving the old cards on screen while Supabase is queried after navigation.
    try:
        load_national_exam_subject_entries(int(st.session_state.national_exam_year))
    except Exception:
        pass


def _queue_national_exam_choice(widget_key, exam_round):
    subject = st.session_state.get(widget_key)
    if subject and subject != "請選擇科目":
        st.session_state.national_exam_pending_choice = (subject, exam_round)


def national_exam_home():
    topbar()
    render_back_button("返回學習", "study", "back_national_exam_home")
    st.markdown('<div class="study-header"><div class="eyebrow">NATIONAL EXAM</div><div class="hero-title" style="font-size:2.05rem">我要刷國考</div><div class="hero-copy">選好年份、考次與科目，再開始這份國考練習。</div></div>', unsafe_allow_html=True)

    current_year = int(st.session_state.national_exam_year)
    with st.container(key="exam_config_card"):
        st.markdown('<div class="card-title" style="font-size:1.12rem;margin-bottom:.8rem">設定這次要練習的考卷</div>', unsafe_allow_html=True)
        selected_year = st.selectbox(
            "年份",
            NATIONAL_EXAM_YEARS,
            index=NATIONAL_EXAM_YEARS.index(current_year) if current_year in NATIONAL_EXAM_YEARS else 0,
            format_func=roc_year_label,
            key="national_exam_year_select",
        )
        st.session_state.national_exam_year = selected_year

        selected_round = st.radio(
            "考次",
            NATIONAL_EXAM_ROUNDS,
            horizontal=True,
            key="national_exam_round_select",
            label_visibility="collapsed",
        )

        try:
            entries = load_national_exam_subject_entries(selected_year)
        except Exception as error:
            st.error("目前無法讀取國考題庫。")
            with st.expander("查看錯誤資訊"):
                st.code(f"{type(error).__name__}: {error}")
            return

        subjects = [item["subject"] for item in entries if item["exam_round"] == selected_round]
        subject_key = f"national_exam_subject_select_{selected_year}_{selected_round}_{st.session_state.national_exam_picker_version}"
        selected_subject = st.selectbox(
            "科目",
            ["請選擇科目"] + subjects,
            index=0,
            key=subject_key,
        )

        if selected_subject != "請選擇科目":
            st.caption(f"{roc_year_label(selected_year)} · {selected_round} · {selected_subject}")

        if st.button(
            "🧪 開始測驗",
            type="primary",
            use_container_width=True,
            disabled=selected_subject == "請選擇科目",
            key="national_exam_start_button",
        ):
            with st.spinner("正在載入國考題目…"):
                try:
                    usable, excluded, total = load_national_exam_paper(selected_year, selected_round, selected_subject)
                except Exception as error:
                    st.session_state.national_exam_load_error = f"{type(error).__name__}: {error}"
                    usable, excluded, total = [], [], 0
            if usable:
                start_national_exam_quiz(usable, selected_year, selected_round, selected_subject, excluded, total)
            elif not st.session_state.national_exam_load_error:
                st.session_state.national_exam_load_error = "這份試卷目前沒有可直接作答的題目。"

    if st.session_state.national_exam_load_error:
        st.error(st.session_state.national_exam_load_error)


def _national_question_progress_state(question_index):
    answer_key = f"exam_answer_{question_index}"
    uncertain_key = f"exam_uncertain_{question_index}"
    widget_answer = st.session_state.get(answer_key)
    answered = question_index in st.session_state.national_exam_answers or widget_answer is not None
    uncertain = bool(st.session_state.get(uncertain_key, st.session_state.national_exam_uncertain.get(question_index, False)))
    if uncertain and not answered:
        return "red"
    if uncertain and answered:
        return "yellow"
    if answered:
        return "green"
    return "gray"


def render_national_exam_progress(current_index, question_count):
    group_size = 10
    current_group = current_index // group_size
    group_count = (question_count + group_size - 1) // group_size

    with st.container(key="exam_group_nav"):
        group_cols = st.columns(group_count)
        for group, col in enumerate(group_cols):
            start = group * group_size
            end = min(start + group_size, question_count)
            states = [_national_question_progress_state(i) for i in range(start, end)]
            if "red" in states:
                base_state = "red"
            elif "yellow" in states:
                base_state = "yellow"
            elif states and all(state == "green" for state in states):
                base_state = "green"
            else:
                base_state = "gray"
            state = f"current_{base_state}" if group == current_group else base_state
            with col:
                if st.button("⌣", key=f"exam_group_{state}_{group}_{current_index}", help=f"跳到第 {start + 1}–{end} 題"):
                    st.session_state.national_exam_index = start
                    st.rerun()

    start = current_group * group_size
    end = min(start + group_size, question_count)
    st.markdown(f'<div class="exam-progress-label">目前區段：第 {start + 1}–{end} 題</div>', unsafe_allow_html=True)

    with st.container(key="exam_small_nav"):
        small_cols = st.columns(end - start)
        for offset, col in enumerate(small_cols):
            question_index = start + offset
            base_state = _national_question_progress_state(question_index)
            state = f"current_{base_state}" if question_index == current_index else base_state
            with col:
                if st.button("⌣", key=f"exam_small_{state}_{question_index}_{current_index}", help=f"跳到第 {question_index + 1} 題"):
                    st.session_state.national_exam_index = question_index
                    st.rerun()


def save_current_national_exam_state(index, options):
    answer_key = f"exam_answer_{index}"
    uncertain_key = f"exam_uncertain_{index}"
    selected = st.session_state.get(answer_key)
    if selected in options:
        st.session_state.national_exam_answers[index] = options.index(selected)
    else:
        st.session_state.national_exam_answers.pop(index, None)
    st.session_state.national_exam_uncertain[index] = bool(st.session_state.get(uncertain_key, False))


def national_exam_unanswered_numbers(question_count):
    return [i + 1 for i in range(question_count) if i not in st.session_state.national_exam_answers]


def show_national_exam_finish_confirmation(missing):
    @st.dialog("要提前結束國考練習嗎？")
    def _dialog():
        st.write(f"還有 {len(missing)} 題未作答。")
        preview = "、".join(map(str, missing[:12]))
        if preview:
            st.caption(f"未作答題目例如：{preview}{'…' if len(missing) > 12 else ''}")
        left, right = st.columns(2)
        with left:
            if st.button("繼續作答", use_container_width=True, key="exam_dialog_continue"):
                st.rerun()
        with right:
            if st.button("仍要結束", type="primary", use_container_width=True, key="exam_dialog_finish"):
                st.session_state.medslime_page = "national_exam_result"
                st.session_state.menu_open = False
                st.rerun()
    _dialog()


def national_exam_quiz_page():
    questions = st.session_state.national_exam_questions or []
    if not questions:
        goto("national_exam")

    topbar()
    render_back_button("返回國考", "national_exam", "back_national_exam_quiz")
    index = max(0, min(st.session_state.national_exam_index, len(questions) - 1))
    question = questions[index]
    options = question["options"]
    official_number = question.get("official_question_number")

    render_national_exam_progress(index, len(questions))
    remaining = sum(1 for i in range(len(questions)) if _national_question_progress_state(i) in ("gray", "red"))
    progress_text = f"第 {index + 1} / {len(questions)} 題 · 尚有 {remaining} 題未作答"
    source_link = ""
    if question.get("source_url"):
        safe_url = html.escape(str(question["source_url"]), quote=True)
        source_link = f'<a class="official-inline-link" href="{safe_url}" target="_blank" rel="noopener noreferrer">官方原題 ↗</a>'
    safe_exam_question = html.escape(normalize_scientific_notation(question["question"]))
    st.markdown(
        f'<div class="quiz-card"><div class="quiz-meta-row"><div class="eyebrow">{progress_text}</div>{source_link}</div><div class="quiz-question">{safe_exam_question}</div></div>',
        unsafe_allow_html=True,
    )

    answer_key = f"exam_answer_{index}"
    uncertain_key = f"exam_uncertain_{index}"
    previous_answer = st.session_state.national_exam_answers.get(index)
    if answer_key not in st.session_state and previous_answer in (0, 1, 2, 3):
        st.session_state[answer_key] = options[previous_answer]
    if uncertain_key not in st.session_state:
        st.session_state[uncertain_key] = bool(st.session_state.national_exam_uncertain.get(index, False))

    selected = st.radio("選擇答案", options, index=None, key=answer_key, label_visibility="collapsed", format_func=normalize_scientific_notation)
    uncertain = st.checkbox("❓ 我不確定這個觀念", key=uncertain_key)
    if selected in options:
        st.session_state.national_exam_answers[index] = options.index(selected)
    else:
        st.session_state.national_exam_answers.pop(index, None)
    st.session_state.national_exam_uncertain[index] = bool(uncertain)

    left, middle, right = st.columns(3)
    with left:
        if index > 0 and st.button("← 上一題", use_container_width=True, key=f"exam_prev_{index}"):
            save_current_national_exam_state(index, options)
            st.session_state.national_exam_index = index - 1
            st.rerun()
    with middle:
        if index < len(questions) - 1 and st.button("下一題 →", type="primary", use_container_width=True, key=f"exam_next_{index}"):
            save_current_national_exam_state(index, options)
            st.session_state.national_exam_index = index + 1
            st.rerun()
    with right:
        if st.button("結束測驗", use_container_width=True, key=f"exam_finish_{index}"):
            save_current_national_exam_state(index, options)
            missing = national_exam_unanswered_numbers(len(questions))
            if missing:
                show_national_exam_finish_confirmation(missing)
            else:
                goto("national_exam_result")


def national_exam_result_page():
    questions = st.session_state.national_exam_questions or []
    if not questions:
        goto("national_exam")
    topbar()
    render_back_button("返回國考", "national_exam", "back_national_exam_result")
    meta = st.session_state.national_exam_meta or {}
    correct = 0
    needs_review = []
    for index, question in enumerate(questions):
        answer = st.session_state.national_exam_answers.get(index)
        uncertain = bool(st.session_state.national_exam_uncertain.get(index, False))
        is_correct = answer == question["correct_index"]
        if is_correct and not uncertain:
            correct += 1
        if (not is_correct) or uncertain:
            needs_review.append((index, question, answer, uncertain, is_correct))

    try:
        save_national_exam_mistakes_if_needed()
    except Exception:
        st.warning("這次錯題暫時無法同步到錯題庫，但測驗結果仍可正常查看。")

    subtitle = f'{roc_year_label(meta.get("exam_year", 2026))} · {meta.get("exam_round", "")} · {html.escape(str(meta.get("subject", "")))}'
    st.markdown(f'<div class="study-header"><div class="eyebrow">RESULT</div><div class="hero-title" style="font-size:2.05rem">完成國考練習</div><div class="hero-copy">{subtitle}<br>真正掌握 {correct} / {len(questions)} 題。</div></div>', unsafe_allow_html=True)

    if not needs_review:
        st.success("這一輪全部掌握！")
    else:
        st.markdown('<div class="section-title">這次需要回頭看的題目</div>', unsafe_allow_html=True)
        for index, question, answer, uncertain, is_correct in needs_review:
            tag = "答對，但不確定" if is_correct and uncertain else "需要訂正"
            official = question.get("official_question_number", index + 1)
            st.markdown(
                f'<div class="result-card"><div class="eyebrow">官方第 {official} 題 · {tag}</div><div class="card-title" style="margin-top:.35rem">{html.escape(normalize_scientific_notation(question["question"]))}</div>{review_options_markup(question, answer)}</div>',
                unsafe_allow_html=True,
            )
            if question.get("explanation"):
                with st.expander("查看解析"):
                    st.markdown(question["explanation"])
            if question.get("source_url"):
                st.link_button("查看官方原題 ↗", question["source_url"])

    left, right = st.columns(2)
    with left:
        if st.button("重新作答", use_container_width=True, key="exam_retry"):
            clear_national_exam_answers()
            goto("national_exam_quiz")
    with right:
        if st.button("回到國考題庫", type="primary", use_container_width=True, key="exam_back_home"):
            goto("national_exam")


def _queue_material_processing(uploaded):
    file_bytes = uploaded.getvalue()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    if st.session_state.material_file_hash == file_hash and st.session_state.material_questions and len(st.session_state.material_questions) == QUIZ_SIZE:
        clear_quiz_answers()
        st.session_state.medslime_page = "quiz"
        st.session_state.menu_open = False
        st.rerun()
    st.session_state.uploaded_learning_file = uploaded.name
    st.session_state.material_pending_bytes = file_bytes
    st.session_state.material_pending_name = uploaded.name
    st.session_state.material_pending_hash = file_hash
    st.session_state.material_generation_error = None
    st.session_state.medslime_page = "material_processing"
    st.session_state.menu_open = False
    st.rerun()


def study_material_intro():
    topbar()
    render_back_button("返回學習", "study", "intro_back")
    with st.container(key="material_intro_card"):
        st.markdown('<div class="intro-art"><div class="mini-slime"><div class="mini-shine"></div><div class="mini-mouth"></div></div><div class="book-stack">📚</div></div><div class="hero-title material-intro-title">上傳教材，AI 生成 10 題<br>開始你的專屬測驗。</div><div class="hero-copy" style="max-width:680px;margin:.8rem auto 0">選好 PDF 後，MedSlime 會直接讀取教材；完成後自動帶你進入第 1 題。</div>', unsafe_allow_html=True)
        with st.container(key="material_intro_uploader"):
            uploaded = st.file_uploader("上傳教材開始學習", type=["pdf"], key="medslime_material_pdf_intro", label_visibility="collapsed")

    if uploaded is None:
        if st.session_state.material_generation_error:
            st.error(st.session_state.material_generation_error)
        return
    _queue_material_processing(uploaded)


def material_processing_page():
    topbar()
    filename = st.session_state.material_pending_name or st.session_state.uploaded_learning_file or "教材.pdf"
    file_bytes = st.session_state.material_pending_bytes
    file_hash = st.session_state.material_pending_hash

    # The loading card is rendered first at the top of its own page, then Streamlit
    # continues with the slower PDF parsing / AI request below.
    render_loading_card(filename)

    if not file_bytes or not file_hash:
        st.session_state.material_generation_error = "找不到待處理的教材，請重新上傳。"
        st.session_state.medslime_page = "study_material_intro"
        st.rerun()

    try:
        _, pages = extract_pdf_text(file_bytes)
        document_text = build_document_text(pages)
        if len(document_text.strip()) < 250:
            raise ValueError("這份 PDF 可讀取的文字太少，可能是掃描檔或圖片型 PDF。")
        payload = generate_material_quiz(document_text)
        st.session_state.material_file_hash = file_hash
        st.session_state.material_subject = payload.get("subject") or "教材測驗"
        st.session_state.material_questions = payload["questions"]
        clear_quiz_answers()
        st.session_state.material_generation_error = None
        st.session_state.material_pending_bytes = None
        st.session_state.material_pending_name = None
        st.session_state.material_pending_hash = None
        st.session_state.medslime_page = "quiz"
        st.session_state.menu_open = False
        st.rerun()
    except Exception as error:
        st.session_state.material_generation_error = f"{type(error).__name__}: {error}"
        st.session_state.material_pending_bytes = None
        st.session_state.material_pending_name = None
        st.session_state.material_pending_hash = None
        st.session_state.medslime_page = "study_material_intro"
        st.rerun()


def study_material_upload():
    topbar()
    if st.button("← 返回介紹", key="upload_back"):
        goto("study_material_intro")
    st.markdown('<div class="study-header"><div class="eyebrow">YOUR MATERIAL</div><div class="hero-title" style="font-size:2.05rem">上傳你的教材</div><div class="hero-copy">選擇 PDF 後會自動生成 10 題並進入測驗，不需要再按一次分析。</div></div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("選擇 PDF 教材", type=["pdf"], key="medslime_material_pdf")

    if uploaded is None:
        if st.session_state.material_generation_error:
            st.error(st.session_state.material_generation_error)
        st.caption("建議使用含有可選取文字的 PDF；掃描型 PDF 之後再加入圖片辨識。")
        return

    _queue_material_processing(uploaded)


# =========================================================
# Quiz
# =========================================================

def save_current_quiz_state(index, options):
    answer_key = f"material_answer_{index}"
    uncertain_key = f"material_uncertain_{index}"
    selected = st.session_state.get(answer_key)
    if selected in options:
        st.session_state.quiz_answers[index] = options.index(selected)
    else:
        st.session_state.quiz_answers.pop(index, None)
    st.session_state.quiz_uncertain[index] = bool(st.session_state.get(uncertain_key, False))


def unanswered_numbers(question_count):
    return [number + 1 for number in range(question_count) if number not in st.session_state.quiz_answers]


def _material_question_progress_state(question_index):
    answer_key = f"material_answer_{question_index}"
    uncertain_key = f"material_uncertain_{question_index}"
    widget_answer = st.session_state.get(answer_key)
    answered = question_index in st.session_state.quiz_answers or widget_answer is not None
    uncertain = bool(st.session_state.get(uncertain_key, st.session_state.quiz_uncertain.get(question_index, False)))
    if uncertain and not answered:
        return "red"
    if uncertain and answered:
        return "yellow"
    if answered:
        return "green"
    return "gray"


def render_material_progress(current_index, question_count):
    with st.container(key="material_small_nav"):
        cols = st.columns(question_count)
        for question_index, col in enumerate(cols):
            base_state = _material_question_progress_state(question_index)
            state = f"current_{base_state}" if question_index == current_index else base_state
            with col:
                if st.button("⌣", key=f"material_small_{state}_{question_index}_{current_index}", help=f"跳到第 {question_index + 1} 題"):
                    st.session_state.quiz_index = question_index
                    st.session_state.quiz_finish_pending = False
                    st.rerun()


def review_options_markup(question, answer):
    letters = ["A", "B", "C", "D"]
    correct_index = question.get("correct_index")
    rows = []
    for idx, option in enumerate(question.get("options", [])):
        cls = "review-option"
        if idx == correct_index:
            cls += " correct"
        elif answer == idx:
            cls += " wrong"
        rows.append(
            f'<div class="{cls}"><span class="review-option-letter">{letters[idx] if idx < 4 else idx + 1}</span>{html.escape(normalize_scientific_notation(option))}</div>'
        )
    return '<div class="review-options">' + ''.join(rows) + '</div>'


def show_finish_confirmation(missing):
    @st.dialog("要提前結束測驗嗎？")
    def _finish_dialog():
        missing_text = "、".join(map(str, missing))
        st.write(f"還有未作答題目：{missing_text}")
        st.caption("你可以回去補答，也可以直接結束這次測驗。")
        left, right = st.columns(2)
        with left:
            if st.button("繼續作答", use_container_width=True, key="dialog_continue_quiz"):
                st.rerun()
        with right:
            if st.button("仍要結束測驗", type="primary", use_container_width=True, key="dialog_force_finish"):
                st.session_state.quiz_finished = True
                st.session_state.quiz_finish_pending = False
                st.session_state.medslime_page = "quiz_result"
                st.session_state.menu_open = False
                st.rerun()
    _finish_dialog()


def material_quiz_page():
    questions = st.session_state.material_questions or []
    if len(questions) != QUIZ_SIZE:
        goto("study_material_upload")

    topbar()
    render_back_button("返回教材", "study_material_intro", "back_material_quiz")
    index = max(0, min(st.session_state.quiz_index, len(questions) - 1))
    question = questions[index]
    options = question["options"]
    safe_question = html.escape(normalize_scientific_notation(question["question"]))

    st.markdown('<div class="quiz-stage">', unsafe_allow_html=True)
    st.markdown(f'<div class="quiz-topline"><span class="quiz-count">第 {index + 1} / {len(questions)} 題</span></div>', unsafe_allow_html=True)
    render_material_progress(index, len(questions))
    st.markdown(f'<div class="quiz-card"><div class="quiz-question">{safe_question}</div></div>', unsafe_allow_html=True)

    answer_key = f"material_answer_{index}"
    uncertain_key = f"material_uncertain_{index}"
    previous_answer = st.session_state.quiz_answers.get(index)
    if answer_key not in st.session_state and previous_answer in (0, 1, 2, 3):
        st.session_state[answer_key] = options[previous_answer]
    if uncertain_key not in st.session_state:
        st.session_state[uncertain_key] = bool(st.session_state.quiz_uncertain.get(index, False))

    selected = st.radio("選擇答案", options, index=None, key=answer_key, label_visibility="collapsed", format_func=normalize_scientific_notation)
    uncertain = st.checkbox("❓ 我不確定這個觀念", key=uncertain_key)

    if selected in options:
        st.session_state.quiz_answers[index] = options.index(selected)
    else:
        st.session_state.quiz_answers.pop(index, None)
    st.session_state.quiz_uncertain[index] = bool(uncertain)

    left, middle, right = st.columns([1, 1, 1])
    with left:
        if index > 0 and st.button("← 上一題", use_container_width=True, key=f"prev_{index}"):
            save_current_quiz_state(index, options)
            st.session_state.quiz_finish_pending = False
            st.session_state.quiz_index = index - 1
            st.rerun()
    with middle:
        if index < len(questions) - 1 and st.button("下一題 →", type="primary", use_container_width=True, key=f"next_{index}"):
            save_current_quiz_state(index, options)
            st.session_state.quiz_finish_pending = False
            st.session_state.quiz_index = index + 1
            st.rerun()
    with right:
        if st.button("結束測驗", use_container_width=True, key=f"finish_{index}"):
            save_current_quiz_state(index, options)
            missing = unanswered_numbers(len(questions))
            if missing:
                show_finish_confirmation(missing)
            else:
                st.session_state.quiz_finished = True
                goto("quiz_result")

    st.markdown("</div>", unsafe_allow_html=True)


def material_quiz_result():
    questions = st.session_state.material_questions or []
    if len(questions) != QUIZ_SIZE:
        goto("study_material_intro")

    topbar()
    render_back_button("返回教材", "study_material_intro", "back_material_result")
    correct = 0
    needs_review = []
    for index, question in enumerate(questions):
        answer = st.session_state.quiz_answers.get(index)
        uncertain = bool(st.session_state.quiz_uncertain.get(index, False))
        is_correct = answer == question["correct_index"]
        if is_correct and not uncertain:
            correct += 1
        if (not is_correct) or uncertain:
            needs_review.append((index, question, answer, uncertain, is_correct))

    try:
        save_material_mistakes_if_needed()
    except Exception:
        st.warning("這次錯題暫時無法同步到錯題庫，但測驗結果仍可正常查看。")

    st.markdown(f'<div class="study-header"><div class="eyebrow">RESULT</div><div class="hero-title" style="font-size:2.05rem">完成 {QUIZ_SIZE} 題測驗</div><div class="hero-copy">真正掌握 {correct} / {QUIZ_SIZE} 題。答對但標記 ❓ 的題目仍會列入複習。</div></div>', unsafe_allow_html=True)

    if not needs_review:
        st.success("全部掌握！這一輪沒有需要複習的題目。")
    else:
        st.markdown('<div class="section-title">這次需要回頭看的題目</div>', unsafe_allow_html=True)
        for index, question, answer, uncertain, is_correct in needs_review:
            tag = "答對，但不確定" if is_correct and uncertain else "需要訂正"
            st.markdown(
                f'<div class="result-card"><div class="eyebrow">Q{index + 1} · {tag}</div><div class="card-title" style="margin-top:.35rem">{html.escape(normalize_scientific_notation(question["question"]))}</div>{review_options_markup(question, answer)}</div>',
                unsafe_allow_html=True,
            )
            with st.expander("查看解析與教材依據"):
                st.markdown(f"**解析**  \n{question['explanation']}")
                if question.get("review_points"):
                    st.markdown("**複習重點**")
                    for point in question["review_points"]:
                        st.markdown(f"- {point}")
                st.markdown(f"**教材來源**  \nPage {question['source_page']}  \n> {question['source_quote']}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("再測一次", use_container_width=True):
            clear_quiz_answers()
            goto("quiz")
    with col2:
        if st.button("回到學習", type="primary", use_container_width=True):
            goto("study")


# =========================================================
# Focus timer / Pomodoro
# =========================================================

FOCUS_COINS_PER_BLOCK = 5
FOCUS_REWARD_BLOCK_SECONDS = 10 * 60
FOCUS_DAILY_COIN_CAP = 30
FOCUS_BREAK_SECONDS = 5 * 60


def _timer_remaining_seconds():
    if st.session_state.focus_status == "running" and st.session_state.focus_end_at:
        return max(0, int(round(st.session_state.focus_end_at - time.time())))
    return max(0, int(st.session_state.focus_remaining_seconds or 0))


def _focus_elapsed_seconds():
    total = max(0, int(st.session_state.focus_total_seconds or 0))
    return max(0, total - _timer_remaining_seconds())


def _award_focus_blocks(elapsed_seconds, toast=True):
    completed_blocks = max(0, int(elapsed_seconds // FOCUS_REWARD_BLOCK_SECONDS))
    new_blocks = completed_blocks - int(st.session_state.focus_rewarded_blocks or 0)
    if new_blocks <= 0:
        return
    potential = new_blocks * FOCUS_COINS_PER_BLOCK
    remaining_cap = max(0, FOCUS_DAILY_COIN_CAP - int(st.session_state.focus_coins_today or 0))
    earned = min(potential, remaining_cap)
    st.session_state.focus_rewarded_blocks = completed_blocks
    if earned <= 0:
        return
    st.session_state.focus_session_coins += earned
    st.session_state.focus_coins_today += earned
    st.session_state.coins += earned
    if toast:
        st.toast(f"專注滿 {completed_blocks * 10} 分鐘，+{earned} 🪙")


def start_focus_round(minutes, new_session=False):
    minutes = max(5, int(minutes))
    if new_session:
        st.session_state.focus_session_coins = 0
        st.session_state.focus_round = 1
    st.session_state.focus_last_duration_minutes = minutes
    st.session_state.focus_phase = "focus"
    st.session_state.focus_status = "running"
    st.session_state.focus_total_seconds = minutes * 60
    st.session_state.focus_remaining_seconds = minutes * 60
    st.session_state.focus_end_at = time.time() + minutes * 60
    st.session_state.focus_rewarded_blocks = 0


def start_break():
    st.session_state.focus_phase = "break"
    st.session_state.focus_status = "running"
    st.session_state.focus_total_seconds = FOCUS_BREAK_SECONDS
    st.session_state.focus_remaining_seconds = FOCUS_BREAK_SECONDS
    st.session_state.focus_end_at = time.time() + FOCUS_BREAK_SECONDS


def start_next_focus_round():
    st.session_state.focus_round += 1
    start_focus_round(st.session_state.focus_last_duration_minutes, new_session=False)


def pause_focus_timer():
    if st.session_state.focus_status != "running":
        return
    st.session_state.focus_remaining_seconds = _timer_remaining_seconds()
    st.session_state.focus_end_at = None
    st.session_state.focus_status = "paused"


def resume_focus_timer():
    if st.session_state.focus_status != "paused":
        return
    remaining = max(1, int(st.session_state.focus_remaining_seconds or 0))
    st.session_state.focus_end_at = time.time() + remaining
    st.session_state.focus_status = "running"


def reset_focus_timer():
    st.session_state.focus_status = "idle"
    st.session_state.focus_phase = "focus"
    st.session_state.focus_total_seconds = st.session_state.focus_last_duration_minutes * 60
    st.session_state.focus_remaining_seconds = st.session_state.focus_total_seconds
    st.session_state.focus_end_at = None
    st.session_state.focus_rewarded_blocks = 0
    st.session_state.focus_session_coins = 0
    st.session_state.focus_round = 1


def stop_focus_timer():
    if st.session_state.focus_phase == "focus" and st.session_state.focus_status in ("running", "paused"):
        elapsed = _focus_elapsed_seconds()
        _award_focus_blocks(elapsed, toast=False)
        st.session_state.focus_seconds_today += elapsed
    reset_focus_timer()


def _format_clock(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def _focus_runner_markup(progress, resting=False, runner_progress=None):
    progress = min(1.0, max(0.0, float(progress)))
    if runner_progress is None:
        runner_progress = progress
    runner_progress = min(1.0, max(0.0, float(runner_progress)))
    left = 6 + runner_progress * 87
    fill = progress * 87
    background = selected_slime_background()
    resting_class = " resting" if resting else ""
    sleep = '<span class="focus-sleep">💤</span>' if resting else ""
    selected_item = slime_data(st.session_state.selected_slime)
    asset_path = Path(f"assets/slimes/{selected_item.get('theme')}.PNG")
    if asset_path.exists():
        art_uri = _local_asset_data_uri(asset_path)
        safe_alt = html.escape(st.session_state.selected_slime)
        runner_class = f"focus-runner has-art{resting_class}"
        runner_inner = f'{sleep}<img class="focus-runner-art" src="{art_uri}" alt="{safe_alt}">'
        runner_style = f"left:{left:.2f}%;"
    else:
        runner_class = f"focus-runner{resting_class}"
        runner_inner = f'{sleep}<div class="focus-runner-mouth"></div>'
        runner_style = f"left:{left:.2f}%;background:{background}"
    return (
        '<div class="focus-path">'
        f'<div class="focus-path-fill" style="width:{fill:.2f}%"></div>'
        f'<div class="{runner_class}" style="{runner_style}">{runner_inner}</div>'
        '<div class="focus-finish">🏁</div></div>'
    )


def show_focus_stop_confirmation():
    @st.dialog("停止這次專注嗎？")
    def _dialog():
        st.write("已完成的專注時間與已拿到的金幣會保留；尚未滿 10 分鐘的區段不會另外給金幣。")
        left, right = st.columns(2)
        with left:
            if st.button("繼續專注", use_container_width=True, key="focus_stop_cancel"):
                st.rerun(scope="app")
        with right:
            if st.button("停止", type="primary", use_container_width=True, key="focus_stop_confirm"):
                stop_focus_timer()
                st.rerun(scope="app")
    _dialog()


@st.fragment(run_every=1)
def render_focus_timer_fragment():
    phase = st.session_state.focus_phase
    status = st.session_state.focus_status
    remaining = _timer_remaining_seconds()

    if phase == "focus" and status == "running":
        elapsed = _focus_elapsed_seconds()
        _award_focus_blocks(elapsed)
        if remaining <= 0:
            _award_focus_blocks(st.session_state.focus_total_seconds)
            st.session_state.focus_seconds_today += st.session_state.focus_total_seconds
            st.toast("🎉 這一輪專注完成！現在休息 5 分鐘。")
            start_break()
            st.rerun()

    if phase == "break" and status == "running" and remaining <= 0:
        st.session_state.focus_remaining_seconds = 0
        st.session_state.focus_end_at = None
        st.session_state.focus_status = "break_done"
        st.rerun()

    phase = st.session_state.focus_phase
    status = st.session_state.focus_status
    remaining = _timer_remaining_seconds()
    total = max(1, int(st.session_state.focus_total_seconds or 1))

    with st.container(key="focus_timer_card"):
        if phase == "focus":
            elapsed = max(0, total - remaining)
            progress = min(1.0, elapsed / total)
            st.markdown(f'<div class="focus-phase">FOCUS · 第 {st.session_state.focus_round} 輪</div><div class="focus-clock">{_format_clock(remaining)}</div>', unsafe_allow_html=True)
            paused_text = " · 已暫停" if status == "paused" else ""
            companion_nickname = st.session_state.slime_nicknames.get(st.session_state.selected_slime, st.session_state.selected_slime)
            st.markdown(f'<div class="focus-sub">{html.escape(companion_nickname)} 正陪你往終點前進{paused_text}</div>', unsafe_allow_html=True)
            st.markdown(_focus_runner_markup(progress, resting=status == "paused"), unsafe_allow_html=True)
            st.markdown(f'<div class="focus-reward-note">每完整 10 分鐘 +{FOCUS_COINS_PER_BLOCK} 🪙，每日最多 {FOCUS_DAILY_COIN_CAP} 🪙　<span class="focus-earned">今天計時器已獲得 {st.session_state.focus_coins_today} 🪙</span></div>', unsafe_allow_html=True)
        else:
            # During break, the slime stays at the finish line while the green bar
            # shrinks from right to left, revealing white space as rest time passes.
            break_fill = min(1.0, max(0.0, remaining / total)) if status in ("running", "paused") else 0.0
            st.markdown(f'<div class="focus-phase">BREAK · 第 {st.session_state.focus_round} 輪完成</div><div class="focus-clock">{_format_clock(remaining)}</div>', unsafe_allow_html=True)
            st.markdown('<div class="focus-sub">休息是番茄鐘的一部分。史萊姆也在終點喘口氣。</div>', unsafe_allow_html=True)
            st.markdown(_focus_runner_markup(break_fill, resting=True, runner_progress=1.0), unsafe_allow_html=True)
            st.markdown(f'<div class="focus-reward-note">休息時間不累積金幣　<span class="focus-earned">今天計時器已獲得 {st.session_state.focus_coins_today} 🪙</span></div>', unsafe_allow_html=True)

        if status == "break_done":
            st.markdown('<div class="focus-done-card"><div class="focus-done-title">休息完成，要再來一輪嗎？</div><div class="muted">下一輪會沿用剛剛的專注時間。</div></div>', unsafe_allow_html=True)
            left, right = st.columns(2)
            with left:
                if st.button("先結束", use_container_width=True, key="focus_break_finish"):
                    reset_focus_timer()
                    st.rerun()
            with right:
                if st.button("開始下一輪 →", type="primary", use_container_width=True, key="focus_next_round"):
                    start_next_focus_round()
                    st.rerun()
            return

        left, middle, right = st.columns(3)
        with left:
            if status == "running":
                if st.button("⏸ 暫停", use_container_width=True, key=f"focus_pause_{phase}"):
                    pause_focus_timer()
                    st.rerun()
            else:
                if st.button("▶ 繼續", type="primary", use_container_width=True, key=f"focus_resume_{phase}"):
                    resume_focus_timer()
                    st.rerun()
        with middle:
            if st.button("■ 停止", use_container_width=True, key=f"focus_stop_{phase}"):
                # A dialog opened directly from a fragment becomes nested fragment UI,
                # which can make its own buttons unresponsive. Request an app-level
                # rerun and let focus_timer_page open the dialog outside the fragment.
                st.session_state.focus_stop_requested = True
                st.rerun(scope="app")
        with right:
            if phase == "break":
                if st.button("跳過休息 →", type="primary", use_container_width=True, key="focus_skip_break"):
                    start_next_focus_round()
                    st.rerun()
            else:
                st.button("休息 5 分鐘", use_container_width=True, disabled=True, key="focus_break_hint")


def focus_timer_page():
    topbar()
    render_back_button("返回學習", "study", "back_focus_timer")
    st.markdown('<div class="study-header"><div class="eyebrow">FOCUS</div><div class="hero-title" style="font-size:2.05rem">和史萊姆一起專心一下。</div><div class="hero-copy">完成一輪專注後會自動進入 5 分鐘休息；想直接繼續也可以跳過休息。</div></div>', unsafe_allow_html=True)

    if st.session_state.focus_status == "idle":
        with st.container(key="focus_setup_card"):
            st.markdown('<div class="card-title" style="font-size:1.15rem;margin-bottom:.75rem">這一輪要專注多久？</div>', unsafe_allow_html=True)
            choice = st.radio("專注時間", ["30 分鐘", "60 分鐘", "自訂"], horizontal=True, key="focus_duration_choice", label_visibility="collapsed")
            if choice == "自訂":
                minutes = st.number_input("自訂分鐘", min_value=5, max_value=120, value=int(st.session_state.focus_last_duration_minutes), step=5, key="focus_custom_minutes")
            else:
                minutes = 30 if choice == "30 分鐘" else 60
            st.markdown(f'<div class="focus-reward-note">每完整 10 分鐘 +{FOCUS_COINS_PER_BLOCK} 🪙，休息時間不計；每天最多從計時器獲得 {FOCUS_DAILY_COIN_CAP} 🪙。</div>', unsafe_allow_html=True)
            if st.button("🍅 開始專注", type="primary", use_container_width=True, key="focus_start"):
                start_focus_round(minutes, new_session=True)
                st.rerun()
        return

    # Open the confirmation dialog at app level, not from inside st.fragment.
    # Pop first so dismissing with X will not cause it to reopen later.
    if st.session_state.pop("focus_stop_requested", False):
        show_focus_stop_confirmation()

    render_focus_timer_fragment()


# =========================================================
# Mistake bank
# =========================================================


def _mistake_filter_rows(rows, source_filter):
    if source_filter == "教材":
        return [row for row in rows if (row.get("source_type") or "ai_document") != "national_exam"]
    if source_filter == "國考":
        return [row for row in rows if row.get("source_type") == "national_exam"]
    return list(rows)


def _mistake_options(row):
    options = row.get("options") or []
    if isinstance(options, str):
        try:
            options = json.loads(options)
        except Exception:
            options = []
    return list(options)


def _mistake_review_points(row):
    points = row.get("review_points") or []
    if isinstance(points, str):
        try:
            points = json.loads(points)
        except Exception:
            points = [points] if points else []
    return list(points)


def _mistake_options_markup(row):
    options = _mistake_options(row)
    user_answer = row.get("user_answer")
    correct_answer = row.get("correct_answer")
    letters = ["A", "B", "C", "D"]
    rendered = []
    for index, option in enumerate(options):
        cls = "review-option"
        if option == correct_answer:
            cls += " correct"
        elif user_answer is not None and option == user_answer:
            cls += " wrong"
        letter = letters[index] if index < len(letters) else str(index + 1)
        rendered.append(
            f'<div class="{cls}"><span class="review-option-letter">{letter}</span>'
            f'{html.escape(normalize_scientific_notation(option))}</div>'
        )
    return '<div class="review-options">' + ''.join(rendered) + '</div>'


def _mistake_source_tag(row):
    return "國考" if row.get("source_type") == "national_exam" else "教材"


def _render_mistake_record(row, reviewed):
    record_id = row.get("id")
    question = normalize_scientific_notation(row.get("question") or "")
    question_number = row.get("official_question_number")
    source_tag = _mistake_source_tag(row)
    state_text = "不確定" if row.get("uncertain") else "答錯"
    number_text = f"第 {question_number} 題 · " if question_number is not None else ""
    preview = question if len(question) <= 58 else question[:58] + "…"
    expander_title = f"{source_tag} · {state_text} · {number_text}{preview}"

    container_key = f"mistake_reviewed_{record_id}" if reviewed else f"mistake_pending_{record_id}"
    with st.container(key=container_key):
        with st.expander(expander_title):
            status_class = "uncertain" if row.get("uncertain") else "wrong"
            reviewed_badge = '<span class="mistake-status reviewed">✓ 已複習</span>' if reviewed else ""
            st.markdown(
                f'<span class="mistake-status {status_class}">{state_text}</span>{reviewed_badge}'
                f'<div class="mistake-row-question">{html.escape(question)}</div>'
                f'{_mistake_options_markup(row)}',
                unsafe_allow_html=True,
            )

            explanation = str(row.get("explanation") or "").strip()
            if explanation:
                st.markdown("**解析**")
                st.write(explanation)

            points = _mistake_review_points(row)
            if points:
                st.markdown("**複習重點**")
                for point in points:
                    st.markdown(f"- {point}")

            source_quote = str(row.get("source_quote") or "").strip()
            if source_quote:
                st.markdown("**教材依據**")
                st.markdown(f"> {source_quote}")

            source = str(row.get("source") or "").strip()
            if source:
                st.markdown(f'<div class="mistake-source">來源：{html.escape(source)}</div>', unsafe_allow_html=True)

            if row.get("source_url"):
                st.link_button("查看官方原題 ↗", row["source_url"])

            if not reviewed:
                if st.button("✓ 已複習", type="primary", key=f"mark_reviewed_{record_id}"):
                    try:
                        mark_mistake_reviewed(record_id)
                        st.rerun()
                    except Exception as error:
                        st.error("目前無法更新複習狀態。")
                        st.caption(f"{type(error).__name__}: {error}")


def mistake_bank_page():
    topbar()
    render_back_button("返回學習", "study", "back_mistakes")
    st.markdown('<div class="study-header"><div class="eyebrow">MISTAKE BANK</div><div class="hero-title" style="font-size:2.05rem">我要複習錯題</div><div class="hero-copy">先選來源，再打開科目資料夾，一題一題把解析看懂。</div></div>', unsafe_allow_html=True)

    filters = ["全部", "教材", "國考"]
    current_filter = st.session_state.mistake_filter if st.session_state.mistake_filter in filters else "全部"
    source_filter = st.radio(
        "錯題來源",
        filters,
        horizontal=True,
        index=filters.index(current_filter),
        key="mistake_source_filter",
        label_visibility="collapsed",
    )
    st.session_state.mistake_filter = source_filter

    try:
        rows = load_mistake_bank()
    except Exception as error:
        st.error("目前無法讀取錯題庫。")
        st.caption(f"{type(error).__name__}: {error}")
        return

    rows = _mistake_filter_rows(rows, source_filter)
    pending_count = sum(1 for row in rows if not _mistake_is_reviewed(row))
    reviewed_count = len(rows) - pending_count
    st.markdown(
        f'<div class="mistake-summary">尚未複習 <strong>{pending_count}</strong> 題 · 已複習 {reviewed_count} 題 · 共 {len(rows)} 題</div>',
        unsafe_allow_html=True,
    )

    if not rows:
        st.info("目前這個分類還沒有錯題。完成教材或國考測驗後，答錯或標記 ❓ 的題目會自動出現在這裡。")
        return

    by_subject = {}
    for row in rows:
        subject = str(row.get("subject") or "未分類")
        by_subject.setdefault(subject, []).append(row)

    subjects = sorted(
        by_subject,
        key=lambda subject: max(_parse_mistake_time(item.get("created_at")) for item in by_subject[subject]),
        reverse=True,
    )

    for index, subject in enumerate(subjects):
        subject_rows = by_subject[subject]
        pending = sum(1 for row in subject_rows if not _mistake_is_reviewed(row))
        label = f"📁  {subject}　·　{pending} 題尚未複習　·　共 {len(subject_rows)} 題　›"
        with st.container(key=f"mistake_folder_row_{index}"):
            if st.button(label, use_container_width=True, key=f"open_mistake_folder_{index}"):
                st.session_state.mistake_subject = subject
                goto("mistake_subject")


def mistake_subject_page():
    subject = st.session_state.mistake_subject
    if not subject:
        goto("mistakes")

    topbar()
    render_back_button("返回錯題庫", "mistakes", "back_mistake_subject")
    source_filter = st.session_state.mistake_filter or "全部"
    st.markdown(
        f'<div class="study-header"><div class="eyebrow">{html.escape(source_filter)}</div>'
        f'<div class="hero-title" style="font-size:2.05rem">📁 {html.escape(str(subject))}</div>'
        f'<div class="hero-copy">尚未複習的題目會排在前面；同一區依完成測驗的時間由新到舊排列。</div></div>',
        unsafe_allow_html=True,
    )

    try:
        rows = load_mistake_bank()
    except Exception as error:
        st.error("目前無法讀取錯題庫。")
        st.caption(f"{type(error).__name__}: {error}")
        return

    rows = [
        row for row in _mistake_filter_rows(rows, source_filter)
        if str(row.get("subject") or "未分類") == str(subject)
    ]
    pending_rows = _sort_mistake_rows([row for row in rows if not _mistake_is_reviewed(row)])
    reviewed_rows = _sort_mistake_rows([row for row in rows if _mistake_is_reviewed(row)])

    st.markdown(f'<div class="section-title">尚未複習 · {len(pending_rows)} 題</div>', unsafe_allow_html=True)
    if not pending_rows:
        st.success("這個資料夾目前沒有尚未複習的題目。")
    for row in pending_rows:
        _render_mistake_record(row, reviewed=False)

    if reviewed_rows:
        st.markdown(f'<div class="section-title">已複習 · {len(reviewed_rows)} 題</div>', unsafe_allow_html=True)
        for row in reviewed_rows:
            _render_mistake_record(row, reviewed=True)


# =========================================================
# Other MVP pages
# =========================================================

def slime_page():
    topbar()
    render_back_button("返回首頁", "home", "back_slime")

    # Keep legacy sessions valid after removing old prototype species.
    catalog_names = {item["name"] for item in SLIME_CATALOG}
    if "青蘋果史萊姆" not in st.session_state.collection:
        st.session_state.collection.append("青蘋果史萊姆")
    if st.session_state.selected_slime not in catalog_names or st.session_state.selected_slime not in st.session_state.collection:
        st.session_state.selected_slime = "青蘋果史萊姆"

    owned = {name for name in st.session_state.collection if name in catalog_names}
    current = slime_data(st.session_state.selected_slime)
    progress = get_slime_progress(current["name"])
    nickname = get_slime_nickname(current["name"])

    st.markdown(
        '<div class="slime-page-header"><div class="eyebrow">MY SLIMES</div>'
        '<div class="hero-title" style="font-size:2.05rem">我的史萊姆</div>'
        '<div class="hero-copy">收藏、培養並選擇今天陪你學習的史萊姆。每一隻都有自己的 Lv. 與 EXP。</div></div>',
        unsafe_allow_html=True,
    )

    action_left, action_right = st.columns(2)
    with action_left:
        if st.button("🎰 前往抽卡", use_container_width=True, key="slime_to_gacha"):
            goto("gacha")
    with action_right:
        if st.button("🏆 查看成就", use_container_width=True, key="slime_to_achievements"):
            goto("achievements")

    rarity_class = f"rarity-{current['rarity']}"
    with st.container(key="companion_panel_live"):
        art_col, info_col = st.columns([1, 3], gap="large", vertical_alignment="center")
        with art_col:
            st.markdown(
                f'<div class="companion-art">{slime_avatar_markup(current, size="hero", selected=True)}</div>',
                unsafe_allow_html=True,
            )
        with info_col:
            st.markdown(
                f'<div class="companion-topline"><span class="rarity-chip {rarity_class}">{current["rarity"]}</span>'
                f'<span class="owned-chip">✓ 陪伴中</span></div>',
                unsafe_allow_html=True,
            )
            # The nickname itself is the edit control, exactly where the name is displayed.
            if st.button(f"{nickname} ✏️", key=f"slime_name_button_{current['theme']}"):
                st.session_state.slime_name_editing = not st.session_state.slime_name_editing
                st.rerun()
            if st.session_state.slime_name_editing:
                with st.container(key=f"slime_nickname_editor_{current['theme']}"):
                    new_nickname = st.text_input("史萊姆暱稱", value=nickname, max_chars=16, key=f"nickname_{current['name']}")
                    save_col, cancel_col = st.columns(2)
                    with save_col:
                        if st.button("儲存名字", type="primary", use_container_width=True, key=f"save_nickname_{current['theme']}"):
                            st.session_state.slime_nicknames[current["name"]] = new_nickname.strip() or current["name"].replace("史萊姆", "")
                            st.session_state.slime_name_editing = False
                            st.rerun()
                    with cancel_col:
                        if st.button("取消", use_container_width=True, key=f"cancel_nickname_{current['theme']}"):
                            st.session_state.slime_name_editing = False
                            st.rerun()
            st.markdown(
                f'<div class="companion-species">{current["name"]} · {current["tagline"]}</div>'
                f'<div class="companion-level-row"><span>Lv.{progress["level"]}</span><span>{progress["exp"]} / 100 EXP</span></div>'
                f'<div class="companion-xp"><span style="width:{min(100, int(progress["exp"]))}%"></span></div>'
                f'<div class="companion-meta"><span>🧩 專屬碎片 {progress.get("fragments", 0)}</span><span>🎨 三階段成長：規劃中</span><span>🎩 裝扮：下一階段</span></div>'
                '<div class="art-placeholder-note">目前角色為介面占位造型；正式美術會在角色設計定稿後替換。</div>',
                unsafe_allow_html=True,
            )

    st.markdown(
        f'<div class="catalog-summary"><div><div class="section-title" style="margin-bottom:.15rem">史萊姆圖鑑</div>'
        f'<div class="catalog-count">已收集 {len(owned)} / {len(SLIME_CATALOG)} 隻</div></div></div>',
        unsafe_allow_html=True,
    )

    dev_preview = st.toggle(
        "🛠️ 開發者預覽",
        value=bool(st.session_state.slime_dev_preview),
        key="slime_dev_preview_toggle",
        help="只解除圖鑑顯示限制，不會把未獲得史萊姆加入收藏。",
    )
    st.session_state.slime_dev_preview = bool(dev_preview)
    if dev_preview:
        st.caption("開發者預覽中：所有普通卡池史萊姆會顯示完整造型與名稱，但持有狀態不變。")

    filters = ["全部", "N", "R", "SR", "SSR", "限定"]
    chosen_filter = st.radio(
        "圖鑑篩選",
        filters,
        index=filters.index(st.session_state.slime_collection_filter) if st.session_state.slime_collection_filter in filters else 0,
        horizontal=True,
        label_visibility="collapsed",
        key="slime_catalog_filter_widget",
    )
    st.session_state.slime_collection_filter = chosen_filter

    if chosen_filter == "限定":
        st.markdown(
            '<div class="limited-empty"><div class="limited-lock">🏆🔒</div>'
            '<div class="card-title" style="font-size:1.15rem">限定史萊姆</div>'
            '<div style="margin-top:.45rem">限定史萊姆不會出現在一般卡池，會和特殊成就直接連動。</div>'
            '<div class="muted" style="margin-top:.5rem">例如：完成整份國考並達成指定分數後解鎖「學霸史萊姆」。角色與條件會在成就系統階段正式加入。</div></div>',
            unsafe_allow_html=True,
        )
        return

    visible_items = SLIME_CATALOG if chosen_filter == "全部" else [item for item in SLIME_CATALOG if item["rarity"] == chosen_filter]
    for row_start in range(0, len(visible_items), 3):
        row = visible_items[row_start:row_start + 3]
        cols = st.columns(3, gap="medium")
        for offset, (col, item) in enumerate(zip(cols, row)):
            index = row_start + offset
            is_owned = item["name"] in owned
            is_selected = item["name"] == st.session_state.selected_slime
            preview_reveal = bool(st.session_state.slime_dev_preview) and not is_owned
            mystery = (item["rarity"] in ("SR", "SSR")) and not is_owned and not preview_reveal
            shown_name = "???" if mystery else item["name"]
            tagline = "抽到後才會揭曉它的真面目。" if mystery else item["tagline"]
            card_progress = get_slime_progress(item["name"]) if is_owned else None
            with col:
                with st.container(key=f"slime_catalog_card_{chosen_filter}_{index}"):
                    if is_selected:
                        st.markdown('<div class="catalog-card-selected"></div>', unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="catalog-art-shell">{slime_avatar_markup(item, size="card", locked=(not is_owned and not preview_reveal), mystery=mystery, selected=is_selected)}</div>'
                        f'<div class="catalog-card-head"><div class="catalog-card-name">{shown_name}</div>'
                        f'<span class="rarity-chip rarity-{item["rarity"]}">{item["rarity"]}</span></div>'
                        f'<div class="catalog-card-tagline">{tagline}</div>'
                        f'<div class="catalog-card-meta"><span>{("Lv." + str(card_progress["level"]) + " · 🧩 " + str(card_progress.get("fragments", 0))) if is_owned else ("🛠️ 開發預覽" if preview_reveal else "🔒 尚未獲得")}</span></div>',
                        unsafe_allow_html=True,
                    )
                    if is_selected:
                        st.button("✓ 陪伴中", disabled=True, use_container_width=True, key=f"slime_selected_{index}_{chosen_filter}")
                    elif is_owned:
                        if st.button("設為陪伴", type="primary", use_container_width=True, key=f"slime_select_{item['theme']}_{chosen_filter}"):
                            st.session_state.selected_slime = item["name"]
                            get_slime_progress(item["name"])
                            get_slime_nickname(item["name"])
                            st.rerun()
                    else:
                        locked_label = "🛠️ 預覽中" if preview_reveal else "🔒 尚未獲得"
                        st.button(locked_label, disabled=True, use_container_width=True, key=f"slime_locked_{item['theme']}_{chosen_filter}")


def achievements_page():
    topbar()
    render_back_button("返回我的史萊姆", "slime", "back_achievements")
    st.markdown("## 🏆 成就")
    unlocked = set(st.session_state.unlocked_achievements)
    st.caption(f"目前解鎖 {len(unlocked)} / {len(ACHIEVEMENTS)}")
    cols = st.columns(3)
    for i, (aid, icon, title, desc, reward) in enumerate(ACHIEVEMENTS):
        unlocked_now = aid in unlocked
        status = "已解鎖" if unlocked_now else "尚未解鎖"
        card_class = "achievement-card" if unlocked_now else "achievement-card locked"
        with cols[i % 3]:
            st.markdown(
                f'<div class="{card_class}"><div class="achievement-icon">{icon}</div>'
                f'<div class="achievement-title">{title}</div>'
                f'<div class="achievement-desc">{desc}</div>'
                f'<div class="achievement-status">{status} · {reward}</div></div>',
                unsafe_allow_html=True,
            )


def gacha_page():
    topbar()
    render_back_button("返回我的史萊姆", "slime", "back_gacha")
    st.markdown("## 🎰 史萊姆召喚")
    st.caption("史萊姆池 · 目前機率暫定 N 60% / R 25% / SR 10% / SSR 5%；正式卡池會在下一階段調整。")
    if st.button("🎫 召喚一次", type="primary", use_container_width=True, disabled=st.session_state.tickets <= 0):
        st.session_state.tickets -= 1
        result = random.choices(GACHA_POOL, weights=[x["weight"] for x in GACHA_POOL], k=1)[0]
        duplicate = result["name"] in st.session_state.collection
        fragments = 0
        refund = 0
        if duplicate:
            fragments = {"N": 1, "R": 2, "SR": 4, "SSR": 8}[result["rarity"]]
            refund = {"N": 10, "R": 20, "SR": 40, "SSR": 80}[result["rarity"]]
            get_slime_progress(result["name"])["fragments"] += fragments
            st.session_state.coins += refund
        else:
            st.session_state.collection.append(result["name"])
            get_slime_progress(result["name"])
            get_slime_nickname(result["name"])
        st.session_state.last_gacha = {**result, "duplicate": duplicate, "fragments": fragments, "refund": refund}
        st.rerun()
    result = st.session_state.last_gacha
    if result:
        msg = (f"重複獲得 · +{result.get('fragments', 0)} 專屬碎片 · +{result.get('refund', 0)} 🪙" if result["duplicate"] else "NEW！已加入收藏")
        st.markdown(f'<div class="gacha-result"><div class="muted">{msg}</div><div style="font-size:5rem">{result["emoji"]}</div><div class="rarity-{result["rarity"]}">{result["rarity"]}</div><div class="card-title">{result["name"]}</div></div>', unsafe_allow_html=True)


page = st.session_state.medslime_page
if page == "home":
    home()
elif page == "study":
    study_home()
elif page == "national_exam":
    national_exam_home()
elif page == "national_exam_quiz":
    national_exam_quiz_page()
elif page == "national_exam_result":
    national_exam_result_page()
elif page == "study_material_intro":
    study_material_intro()
elif page == "study_material_upload":
    study_material_upload()
elif page == "material_processing":
    material_processing_page()
elif page == "quiz":
    material_quiz_page()
elif page == "quiz_result":
    material_quiz_result()
elif page == "focus_timer":
    focus_timer_page()
elif page == "mistakes":
    mistake_bank_page()
elif page == "mistake_subject":
    mistake_subject_page()
elif page == "slime":
    slime_page()
elif page == "gacha":
    gacha_page()
elif page == "achievements":
    achievements_page()
else:
    st.session_state.medslime_page = "home"
    st.rerun()
