import hashlib
import html
import json
import random
from io import BytesIO

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

GACHA_POOL = [
    {"name": "青蘋果史萊姆", "rarity": "N", "emoji": "🟢", "weight": 35},
    {"name": "薄荷史萊姆", "rarity": "N", "emoji": "🟩", "weight": 35},
    {"name": "藍莓史萊姆", "rarity": "R", "emoji": "🔵", "weight": 14},
    {"name": "葡萄史萊姆", "rarity": "R", "emoji": "🟣", "weight": 11},
    {"name": "黃金史萊姆", "rarity": "SSR", "emoji": "🟡", "weight": 4},
    {"name": "星空史萊姆", "rarity": "SSR", "emoji": "🌌", "weight": 1},
]


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

    [data-testid="stHorizontalBlock"]:has([class*="st-key-nav_toggle"]) { flex-wrap:nowrap !important; align-items:center !important; gap:.35rem !important; }
    [data-testid="stHorizontalBlock"]:has([class*="st-key-nav_toggle"]) > div:nth-child(1) { min-width:46px !important; width:46px !important; flex:0 0 46px !important; }
    [data-testid="stHorizontalBlock"]:has([class*="st-key-nav_toggle"]) > div:nth-child(2) { min-width:145px !important; flex:1 1 auto !important; }
    [data-testid="stHorizontalBlock"]:has([class*="st-key-nav_toggle"]) > div:nth-child(3) { min-width:0 !important; flex:0 1 auto !important; margin-left:auto !important; }
    [class*="st-key-nav_toggle"] button { width:42px !important; height:42px !important; min-width:42px !important; min-height:42px !important; padding:0 !important; border:none !important; border-radius:12px !important; background:#17372a !important; color:white !important; box-shadow:0 5px 14px rgba(23,55,42,.15) !important; font-size:1.2rem !important; }
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

    .choice-card { background:rgba(255,255,255,.96); border:1px solid #dceae2; border-radius:25px; padding:1.45rem 1.5rem; min-height:156px; box-shadow:0 12px 28px rgba(30,78,50,.055); }
    .choice-icon-shell { width:50px; height:50px; border-radius:15px; display:flex; align-items:center; justify-content:center; background:linear-gradient(145deg,#e8f9ee,#f1fbf5); border:1px solid #d7eadf; margin-bottom:.9rem; }
    .choice-icon { font-size:1.72rem; }
    .choice-title { font-size:1.17rem; font-weight:950; color:#173b2b; }
    .choice-copy { color:#70877a; line-height:1.55; margin-top:.42rem; }
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
    .exam-group-track { display:flex; justify-content:center; align-items:center; gap:.7rem; flex-wrap:wrap; margin:.25rem 0 .45rem; }
    .exam-group-slime { width:38px; height:30px; border-radius:50% 50% 42% 42%/62% 62% 38% 38%; background:#e3eee7; border:1px solid #d1e1d7; position:relative; opacity:.62; }
    .exam-group-slime.done { background:linear-gradient(145deg,#84e5a3,#43c879); opacity:1; }
    .exam-group-slime.current { background:linear-gradient(145deg,#9af0b3,#35c878); border-color:#31bd70; opacity:1; transform:scale(1.15); box-shadow:0 0 0 4px rgba(49,201,120,.12); }
    .exam-group-slime:before,.exam-group-slime:after { content:""; position:absolute; top:40%; width:4px; height:6px; border-radius:50%; background:#173b2b; }
    .exam-group-slime:before { left:29%; }
    .exam-group-slime:after { right:29%; }
    .exam-progress-label { text-align:center; color:#688476; font-size:.85rem; font-weight:800; margin:.35rem 0 .1rem; }
    [class*="st-key-exam_year_"] button { min-height:68px !important; font-size:1.02rem !important; }
    [class*="st-key-exam_subject_"] button { min-height:70px !important; white-space:normal !important; line-height:1.4 !important; }
    .quiz-card { background:rgba(255,255,255,.96); border:1px solid #dceae2; border-radius:27px; padding:1.55rem 1.6rem; box-shadow:0 14px 34px rgba(31,83,53,.06); animation:questionIn .22s ease-out both; margin-bottom:.8rem; }
    .quiz-question { color:#173b2b; font-size:1.22rem; line-height:1.65; font-weight:850; }

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
    [data-testid="stExpander"] { background:rgba(255,255,255,.92) !important; border:1px solid #dceae2 !important; border-radius:14px !important; overflow:hidden; }
    [data-testid="stExpander"] summary,
    [data-testid="stExpander"] summary p,
    [data-testid="stExpander"] summary span,
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"],
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stExpander"] [data-testid="stMarkdownContainer"] li,
    [data-testid="stExpander"] [data-testid="stCaptionContainer"] { color:#244c39 !important; opacity:1 !important; }

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

    .home-copy-card,.home-slime-card,.home-task,.choice-card,.study-header,.intro-panel { animation:pageIn .20s ease-out both; }
    @keyframes drawerIn { from { transform:translateX(-18px); opacity:0; } to { transform:translateX(0); opacity:1; } }
    @keyframes pageIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
    @keyframes questionIn { from { opacity:0; transform:translateX(9px); } to { opacity:1; transform:translateX(0); } }
    @keyframes slimeBounce { 0%,100% { transform:translateY(0) scaleX(1); } 45% { transform:translateY(-8px) scaleX(.97); } 60% { transform:translateY(-5px) scaleX(1.03); } }
    @keyframes dots { 0%,70%,100% { opacity:.28; transform:translateY(0); } 35% { opacity:1; transform:translateY(-3px); } }
    @keyframes progressSlime { 0% { transform:scale(.94); } 65% { transform:scale(1.19); } 100% { transform:scale(1.14); } }

    @media (max-width:700px) {
        .block-container { padding-left:.85rem; padding-right:.85rem; padding-bottom:3rem; }
        .hero-title { font-size:1.9rem; }
        .home-copy-card,.home-slime-card { min-height:auto; }
        .choice-card { min-height:145px; padding:1.2rem; }
        .intro-panel { padding:1.45rem 1.1rem; }
        .quiz-card { padding:1.2rem 1.1rem; }
        .quiz-question { font-size:1.08rem; }
        .slime-track { grid-template-columns:repeat(10, minmax(19px, 30px)); gap:.22rem; padding:.4rem 0 1rem; }
        [data-testid="stHorizontalBlock"]:has([class*="st-key-nav_toggle"]) { gap:.18rem !important; }
        [data-testid="stHorizontalBlock"]:has([class*="st-key-nav_toggle"]) > div:nth-child(1) { min-width:42px !important; width:42px !important; flex:0 0 42px !important; }
        [data-testid="stHorizontalBlock"]:has([class*="st-key-nav_toggle"]) > div:nth-child(2) { min-width:112px !important; }
        [class*="st-key-nav_toggle"] button { width:38px !important; height:38px !important; min-width:38px !important; min-height:38px !important; font-size:1.05rem !important; }
        [class*="st-key-brand_home_"] button,[class*="st-key-brand_home_"] button p { min-height:42px !important; line-height:42px !important; font-size:1.25rem !important; }
        .currency { min-height:42px; gap:.15rem; }
        .pill { min-height:31px; padding:.23rem .32rem; font-size:.67rem; box-shadow:none; }
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


def render_drawer():
    if not st.session_state.menu_open:
        return
    active = st.session_state.medslime_page
    if active.startswith("study_material") or active.startswith("quiz") or active.startswith("national_exam"):
        active = "study"
    items = [
        ("home", "🏠  首頁"),
        ("study", "📖  學習"),
        ("slime", "🐾  史萊姆"),
        ("gacha", "🎰  抽卡"),
        ("achievements", "🏆  成就"),
    ]
    with st.container(key="nav_drawer"):
        close_col, _ = st.columns([1, 5])
        with close_col:
            if st.button("✕", key="drawer_close"):
                st.session_state.menu_open = False
                st.rerun()
        st.markdown('<div class="drawer-title">MedSlime<span style="color:#31b96c">.</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="drawer-note">選擇你要前往的地方</div>', unsafe_allow_html=True)
        for page, label in items:
            if st.button(label, key=f"drawer_{page}", use_container_width=True, type="primary" if page == active else "secondary"):
                goto(page)


def topbar():
    menu_col, brand_col, currency_col = st.columns([0.12, 1, 2.1], vertical_alignment="center")
    with menu_col:
        if st.button("☰", key="nav_toggle", help="開啟選單"):
            st.session_state.menu_open = True
            st.rerun()
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
    left, right = st.columns([1.35, 1], gap="large", vertical_alignment="center")
    with left:
        st.markdown('<div class="home-copy-card"><div class="eyebrow">TODAY’S STUDY</div><div class="hero-title">把今天的知識<br>餵給你的史萊姆。</div><div class="hero-copy">做題、訂正與專注學習都會讓史萊姆成長。先完成一小段，再去看看今天能不能拿到新的抽卡券。</div></div>', unsafe_allow_html=True)
        if st.button("🧠 開始學習", type="primary", use_container_width=True, key="home_start_study"):
            goto("study")
    with right:
        st.markdown('<div class="home-slime-card">' + slime_markup() + f'<div class="home-slime-label">{st.session_state.slime_name} · Lv.{st.session_state.player_level}</div><div class="home-xp"><div class="home-xp-fill" style="width:{st.session_state.player_exp}%"></div></div><div class="muted">{st.session_state.player_exp} / 100 EXP · {st.session_state.selected_slime}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">今日任務</div>', unsafe_allow_html=True)
    tasks = [
        ("🧠", "完成 5 題", "0 / 5", "+20 EXP"),
        ("🔍", "訂正 1 題", "0 / 1", "+50 🪙"),
        ("⏱️", "學習 20 分鐘", "0 / 20", "+1 🎫"),
    ]
    cols = st.columns(3, gap="medium")
    for col, (icon, title, progress, reward) in zip(cols, tasks):
        with col:
            st.markdown(f'<div class="home-task"><div class="task-icon">{icon}</div><div class="card-title">{title}</div><div class="muted">{progress}</div><div class="task-reward">{reward}</div></div>', unsafe_allow_html=True)


def study_home():
    topbar()
    st.markdown('<div class="study-header"><div class="eyebrow">STUDY</div><div class="hero-title" style="font-size:2.05rem">你想怎麼學習呢？</div><div class="hero-copy">選擇適合你現在狀態的方式，MedSlime 陪你一起進步。</div></div>', unsafe_allow_html=True)
    rows = [
        [("📄", "我有教材", "上傳 PDF 教材，AI 會直接生成 10 題並開始測驗。", "study_material_intro"), ("🧪", "我要刷國考", "練習歷屆國考題目，快速檢測實力與弱點。", "national_exam")],
        [("📘", "我要複習錯題", "回顧答錯或不確定的題目，加強你的弱點。", None), ("⏱️", "我要專心讀書", "進入專注計時器，累積今天的學習效率。", None)],
    ]
    for row in rows:
        cols = st.columns(2, gap="large")
        for col, (icon, title, copy, target) in zip(cols, row):
            with col:
                st.markdown(f'<div class="choice-card"><div class="choice-icon-shell"><div class="choice-icon">{icon}</div></div><div class="choice-title">{title}</div><div class="choice-copy">{copy}</div></div>', unsafe_allow_html=True)
                if target:
                    if st.button(f"進入 {title} →", key=f"go_{target}", use_container_width=True, type="primary"):
                        goto(target)
                else:
                    st.button("即將開放", key=f"soon_{title}", use_container_width=True, disabled=True)
        st.write("")


def national_exam_home():
    topbar()
    st.markdown('<div class="study-header"><div class="eyebrow">NATIONAL EXAM</div><div class="hero-title" style="font-size:2.05rem">我要刷國考</div><div class="hero-copy">先選年份，再選科目；點下科目後直接開始第 1 題。</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title" style="margin-top:.9rem">① 選擇年份</div>', unsafe_allow_html=True)
    years = NATIONAL_EXAM_YEARS
    year_cols = st.columns(5)
    selected_year = int(st.session_state.national_exam_year)
    for i, year in enumerate(years):
        with year_cols[i % 5]:
            if st.button(
                roc_year_label(year),
                key=f"exam_year_{year}",
                use_container_width=True,
                type="primary" if year == selected_year else "secondary",
            ):
                st.session_state.national_exam_year = year
                st.session_state.national_exam_load_error = None
                st.rerun()

    st.markdown(f'<div class="section-title">② 選擇科目 · {roc_year_label(selected_year)}</div>', unsafe_allow_html=True)
    try:
        entries = load_national_exam_subject_entries(selected_year)
    except Exception as error:
        st.error("目前無法讀取國考題庫。")
        with st.expander("查看錯誤資訊"):
            st.code(f"{type(error).__name__}: {error}")
        return

    if not entries:
        st.info("這個年份目前沒有可用的國考科目。")
        return

    subject_cols = st.columns(3)
    for i, entry in enumerate(entries):
        subject = entry["subject"]
        exam_round = entry["exam_round"]
        with subject_cols[i % 3]:
            label = f"{subject} · {exam_round}"
            if st.button(label, key=f"exam_subject_{selected_year}_{i}", use_container_width=True):
                with st.spinner("正在載入國考題目…"):
                    try:
                        usable, excluded, total = load_national_exam_paper(selected_year, exam_round, subject)
                    except Exception as error:
                        st.session_state.national_exam_load_error = f"{type(error).__name__}: {error}"
                        st.rerun()
                if not usable:
                    st.session_state.national_exam_load_error = "這份試卷目前沒有可直接作答的題目。"
                    st.rerun()
                start_national_exam_quiz(usable, selected_year, exam_round, subject, excluded, total)

    if st.session_state.national_exam_load_error:
        st.error(st.session_state.national_exam_load_error)


def national_exam_progress_markup(current_index, question_count):
    answers = st.session_state.national_exam_answers
    group_size = 10
    current_group = current_index // group_size
    group_count = (question_count + group_size - 1) // group_size
    groups = []
    for group in range(group_count):
        start = group * group_size
        end = min(start + group_size, question_count)
        if group == current_group:
            state = "current"
        elif all(i in answers for i in range(start, end)):
            state = "done"
        else:
            state = "future"
        groups.append(f'<div class="exam-group-slime {state}" title="第 {start + 1}–{end} 題"></div>')

    start = current_group * group_size
    end = min(start + group_size, question_count)
    minis = []
    for i in range(start, end):
        if i == current_index:
            state = "current"
        elif i in answers:
            state = "done"
        else:
            state = "future"
        minis.append(f'<div class="mini-progress-slime {state}" title="第 {i + 1} 題"><span class="mini-progress-mouth"></span></div>')

    return (
        '<div class="exam-group-track">' + ''.join(groups) + '</div>'
        + f'<div class="exam-progress-label">目前區段：第 {start + 1}–{end} 題</div>'
        + '<div class="slime-track">' + ''.join(minis) + '</div>'
    )


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
    index = max(0, min(st.session_state.national_exam_index, len(questions) - 1))
    question = questions[index]
    options = question["options"]
    official_number = question.get("official_question_number")

    st.markdown(f'<div class="quiz-topline"><span class="quiz-count">第 {index + 1} / {len(questions)} 題</span></div>', unsafe_allow_html=True)
    st.markdown(national_exam_progress_markup(index, len(questions)), unsafe_allow_html=True)
    official = f'<div class="eyebrow">官方第 {official_number} 題</div>' if official_number is not None else ''
    st.markdown(f'<div class="quiz-card">{official}<div class="quiz-question" style="margin-top:.25rem">{html.escape(str(question["question"]))}</div></div>', unsafe_allow_html=True)

    answer_key = f"exam_answer_{index}"
    uncertain_key = f"exam_uncertain_{index}"
    previous_answer = st.session_state.national_exam_answers.get(index)
    if answer_key not in st.session_state and previous_answer in (0, 1, 2, 3):
        st.session_state[answer_key] = options[previous_answer]
    if uncertain_key not in st.session_state:
        st.session_state[uncertain_key] = bool(st.session_state.national_exam_uncertain.get(index, False))

    selected = st.radio("選擇答案", options, index=None, key=answer_key, label_visibility="collapsed")
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

    subtitle = f'{roc_year_label(meta.get("exam_year", 2026))} · {meta.get("exam_round", "")} · {html.escape(str(meta.get("subject", "")))}'
    st.markdown(f'<div class="study-header"><div class="eyebrow">RESULT</div><div class="hero-title" style="font-size:2.05rem">完成國考練習</div><div class="hero-copy">{subtitle}<br>真正掌握 {correct} / {len(questions)} 題。</div></div>', unsafe_allow_html=True)

    if not needs_review:
        st.success("這一輪全部掌握！")
    else:
        st.markdown('<div class="section-title">這次需要回頭看的題目</div>', unsafe_allow_html=True)
        for index, question, answer, uncertain, is_correct in needs_review:
            correct_text = question["options"][question["correct_index"]]
            your_text = question["options"][answer] if answer in (0, 1, 2, 3) else "未作答"
            tag = "答對，但不確定" if is_correct and uncertain else "需要訂正"
            official = question.get("official_question_number", index + 1)
            st.markdown(f'<div class="result-card"><div class="eyebrow">官方第 {official} 題 · {tag}</div><div class="card-title" style="margin-top:.35rem">{html.escape(str(question["question"]))}</div><div class="muted" style="margin-top:.65rem">你的答案：{html.escape(str(your_text))}</div><div style="margin-top:.25rem;color:#248c56;font-weight:850">正確答案：{html.escape(str(correct_text))}</div></div>', unsafe_allow_html=True)
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


def study_material_intro():
    topbar()
    if st.button("← 返回學習", key="intro_back"):
        goto("study")
    st.markdown('<div class="intro-panel"><div class="intro-art"><div class="mini-slime"><div class="mini-shine"></div><div class="mini-mouth"></div></div><div class="book-stack">📚</div></div><div class="hero-title" style="font-size:2rem">上傳教材，AI 直接生成 10 題<br>開始你的專屬測驗。</div><div class="hero-copy" style="max-width:680px;margin:.8rem auto 0">選好 PDF 後，MedSlime 會讀取教材並直接準備題目；完成後自動帶你進入第 1 題。</div></div>', unsafe_allow_html=True)
    if st.button("☁️ 上傳教材開始學習", type="primary", use_container_width=True):
        prepare_material_upload()
        goto("study_material_upload")


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

    file_bytes = uploaded.getvalue()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    if st.session_state.material_file_hash == file_hash and st.session_state.material_questions and len(st.session_state.material_questions) == QUIZ_SIZE:
        clear_quiz_answers()
        goto("quiz")

    st.session_state.uploaded_learning_file = uploaded.name
    st.session_state.material_generation_error = None
    loading = st.empty()
    with loading.container():
        render_loading_card(uploaded.name)

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
        loading.empty()
        goto("quiz")
    except Exception as error:
        loading.empty()
        st.session_state.material_generation_error = f"{type(error).__name__}: {error}"
        st.error("教材處理失敗，請重新上傳或稍後再試。")
        with st.expander("查看錯誤資訊"):
            st.code(st.session_state.material_generation_error)


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


def slime_progress_markup(current_index, question_count):
    slimes = []
    for number in range(question_count):
        if number == current_index:
            state = "current"
        elif number in st.session_state.quiz_answers:
            state = "done"
        else:
            state = "future"
        slimes.append(
            f'<div class="mini-progress-slime {state}" title="第 {number + 1} 題">'
            '<span class="mini-progress-mouth"></span></div>'
        )
    return '<div class="slime-track">' + "".join(slimes) + '</div>'


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
    index = max(0, min(st.session_state.quiz_index, len(questions) - 1))
    question = questions[index]
    options = question["options"]
    safe_question = html.escape(str(question["question"]))

    st.markdown('<div class="quiz-stage">', unsafe_allow_html=True)
    st.markdown(f'<div class="quiz-topline"><span class="quiz-count">第 {index + 1} / {len(questions)} 題</span></div>', unsafe_allow_html=True)
    st.markdown(slime_progress_markup(index, len(questions)), unsafe_allow_html=True)
    st.markdown(f'<div class="quiz-card"><div class="quiz-question">{safe_question}</div></div>', unsafe_allow_html=True)

    answer_key = f"material_answer_{index}"
    uncertain_key = f"material_uncertain_{index}"
    previous_answer = st.session_state.quiz_answers.get(index)
    if answer_key not in st.session_state and previous_answer in (0, 1, 2, 3):
        st.session_state[answer_key] = options[previous_answer]
    if uncertain_key not in st.session_state:
        st.session_state[uncertain_key] = bool(st.session_state.quiz_uncertain.get(index, False))

    selected = st.radio("選擇答案", options, index=None, key=answer_key, label_visibility="collapsed")
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
        goto("study_material_upload")

    topbar()
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

    st.markdown(f'<div class="study-header"><div class="eyebrow">RESULT</div><div class="hero-title" style="font-size:2.05rem">完成 {QUIZ_SIZE} 題測驗</div><div class="hero-copy">真正掌握 {correct} / {QUIZ_SIZE} 題。答對但標記 ❓ 的題目仍會列入複習。</div></div>', unsafe_allow_html=True)

    if not needs_review:
        st.success("全部掌握！這一輪沒有需要複習的題目。")
    else:
        st.markdown('<div class="section-title">這次需要回頭看的題目</div>', unsafe_allow_html=True)
        for index, question, answer, uncertain, is_correct in needs_review:
            correct_text = question["options"][question["correct_index"]]
            your_text = question["options"][answer] if answer in (0, 1, 2, 3) else "未作答"
            tag = "答對，但不確定" if is_correct and uncertain else "需要訂正"
            st.markdown(f'<div class="result-card"><div class="eyebrow">Q{index + 1} · {tag}</div><div class="card-title" style="margin-top:.35rem">{html.escape(str(question["question"]))}</div><div class="muted" style="margin-top:.65rem">你的答案：{html.escape(str(your_text))}</div><div style="margin-top:.25rem;color:#248c56;font-weight:850">正確答案：{html.escape(str(correct_text))}</div></div>', unsafe_allow_html=True)
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
# Other MVP pages
# =========================================================

def slime_page():
    topbar()
    st.markdown("## 🐾 我的史萊姆")
    left, right = st.columns([1, 1.35], gap="large")
    with left:
        st.markdown('<div style="text-align:center;padding:1.2rem;background:white;border:1px solid #dfebe4;border-radius:24px">' + slime_markup() + '</div>', unsafe_allow_html=True)
        st.session_state.slime_name = st.text_input("史萊姆名字", value=st.session_state.slime_name, max_chars=16)
    with right:
        st.markdown("### 收藏")
        for slime in st.session_state.collection:
            if st.button(("✅ " if slime == st.session_state.selected_slime else "🟢 ") + slime, key=f"slime_{slime}", use_container_width=True):
                st.session_state.selected_slime = slime
                st.rerun()


def achievements_page():
    topbar()
    st.markdown("## 🏆 成就")
    unlocked = set(st.session_state.unlocked_achievements)
    st.caption(f"目前解鎖 {len(unlocked)} / {len(ACHIEVEMENTS)}")
    cols = st.columns(3)
    for i, (aid, icon, title, desc, reward) in enumerate(ACHIEVEMENTS):
        style = "opacity:1" if aid in unlocked else "filter:grayscale(.8);opacity:.55"
        status = "已解鎖" if aid in unlocked else "尚未解鎖"
        with cols[i % 3]:
            st.markdown(f'<div style="{style};background:white;border:1px solid #dfebe4;border-radius:22px;padding:1rem;min-height:150px"><div style="font-size:2rem">{icon}</div><div class="card-title">{title}</div><div class="muted">{desc}</div><div style="margin-top:.6rem;font-weight:850">{status} · {reward}</div></div><br>', unsafe_allow_html=True)


def gacha_page():
    topbar()
    st.markdown("## 🎰 史萊姆召喚")
    st.caption("1 張抽卡券 = 1 次召喚 · N 70% · R 25% · SSR 5%")
    if st.button("🎫 召喚一次", type="primary", use_container_width=True, disabled=st.session_state.tickets <= 0):
        st.session_state.tickets -= 1
        result = random.choices(GACHA_POOL, weights=[x["weight"] for x in GACHA_POOL], k=1)[0]
        duplicate = result["name"] in st.session_state.collection
        if duplicate:
            st.session_state.coins += 50 if result["rarity"] == "N" else 120 if result["rarity"] == "R" else 300
        else:
            st.session_state.collection.append(result["name"])
        st.session_state.last_gacha = {**result, "duplicate": duplicate}
        st.rerun()
    result = st.session_state.last_gacha
    if result:
        msg = "重複獲得，已轉換成金幣" if result["duplicate"] else "NEW！已加入收藏"
        st.markdown(f'<div class="gacha-result"><div class="muted">{msg}</div><div style="font-size:5rem">{result["emoji"]}</div><div class="rarity-{result["rarity"]}">{result["rarity"]}</div><div class="card-title">{result["name"]}</div></div>', unsafe_allow_html=True)


render_drawer()

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
elif page == "quiz":
    material_quiz_page()
elif page == "quiz_result":
    material_quiz_result()
elif page == "slime":
    slime_page()
elif page == "gacha":
    gacha_page()
elif page == "achievements":
    achievements_page()
else:
    st.session_state.medslime_page = "home"
    st.rerun()
