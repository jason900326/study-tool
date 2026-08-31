from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 match, got {count}')
    text = text.replace(old, new, 1)

# Import Supabase client.
replace_once(
    'from pypdf import PdfReader\n',
    'from pypdf import PdfReader\nfrom supabase import create_client\n',
    'supabase import',
)

# Add independent national-exam state.
replace_once(
    '    "quiz_finish_pending": False,\n}',
    '    "quiz_finish_pending": False,\n    "national_exam_year": 2026,\n    "national_exam_questions": None,\n    "national_exam_meta": None,\n    "national_exam_index": 0,\n    "national_exam_answers": {},\n    "national_exam_uncertain": {},\n    "national_exam_excluded": [],\n    "national_exam_total": 0,\n    "national_exam_load_error": None,\n}',
    'national exam session state',
)

adapter = r'''

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
'''

replace_once(
    '\n\n# =========================================================\n# Style\n# =========================================================\n',
    adapter + '\n\n# =========================================================\n# Style\n# =========================================================\n',
    'insert national exam adapter',
)

# Exam-specific visuals.
replace_once(
    '    .mini-progress-slime.future .mini-progress-mouth { opacity:.22; }\n    .quiz-card',
    '''    .mini-progress-slime.future .mini-progress-mouth { opacity:.22; }\n    .exam-group-track { display:flex; justify-content:center; align-items:center; gap:.7rem; flex-wrap:wrap; margin:.25rem 0 .45rem; }\n    .exam-group-slime { width:38px; height:30px; border-radius:50% 50% 42% 42%/62% 62% 38% 38%; background:#e3eee7; border:1px solid #d1e1d7; position:relative; opacity:.62; }\n    .exam-group-slime.done { background:linear-gradient(145deg,#84e5a3,#43c879); opacity:1; }\n    .exam-group-slime.current { background:linear-gradient(145deg,#9af0b3,#35c878); border-color:#31bd70; opacity:1; transform:scale(1.15); box-shadow:0 0 0 4px rgba(49,201,120,.12); }\n    .exam-group-slime:before,.exam-group-slime:after { content:\"\"; position:absolute; top:40%; width:4px; height:6px; border-radius:50%; background:#173b2b; }\n    .exam-group-slime:before { left:29%; }\n    .exam-group-slime:after { right:29%; }\n    .exam-progress-label { text-align:center; color:#688476; font-size:.85rem; font-weight:800; margin:.35rem 0 .1rem; }\n    [class*=\"st-key-exam_year_\"] button { min-height:68px !important; font-size:1.02rem !important; }\n    [class*=\"st-key-exam_subject_\"] button { min-height:70px !important; white-space:normal !important; line-height:1.4 !important; }\n    .quiz-card''',
    'exam CSS',
)

# Drawer should regard national exam as Study.
replace_once(
    '    if active.startswith("study_material") or active.startswith("quiz"):\n        active = "study"',
    '    if active.startswith("study_material") or active.startswith("quiz") or active.startswith("national_exam"):\n        active = "study"',
    'drawer active national exam',
)

# Enable national-exam entry card.
replace_once(
    '("🧪", "我要刷國考", "練習歷屆國考題目，快速檢測實力與弱點。", None)',
    '("🧪", "我要刷國考", "練習歷屆國考題目，快速檢測實力與弱點。", "national_exam")',
    'enable national exam card',
)

ui = r'''

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
'''

replace_once(
    '\n\ndef study_material_intro():',
    ui + '\n\ndef study_material_intro():',
    'insert national exam UI',
)

# Routes.
replace_once(
    'elif page == "study_material_intro":\n    study_material_intro()',
    'elif page == "national_exam":\n    national_exam_home()\nelif page == "national_exam_quiz":\n    national_exam_quiz_page()\nelif page == "national_exam_result":\n    national_exam_result_page()\nelif page == "study_material_intro":\n    study_material_intro()',
    'national exam routes',
)

path.write_text(text, encoding='utf-8')
print('National exam flow patched successfully')
