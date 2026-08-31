from pathlib import Path

path = Path("streamlit_app.py")
text = path.read_text(encoding="utf-8")


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, got {count}")
    text = text.replace(old, new, 1)


# Extra picker state: the version lets us return to a fresh subject dropdown
# without mutating a Streamlit widget key after it has been instantiated.
replace_once(
    '    "national_exam_load_error": None,\n}',
    '    "national_exam_load_error": None,\n    "national_exam_pending_choice": None,\n    "national_exam_picker_version": 0,\n}',
    "national exam picker state",
)

# Starting a quiz advances the picker version, so returning to the exam home
# always shows clean subject dropdowns instead of auto-starting the last paper.
replace_once(
    '    st.session_state.national_exam_total = total\n    clear_national_exam_answers()\n',
    '    st.session_state.national_exam_total = total\n    st.session_state.national_exam_pending_choice = None\n    st.session_state.national_exam_picker_version += 1\n    clear_national_exam_answers()\n',
    "picker version on quiz start",
)

old_css = '''    .exam-group-track { display:flex; justify-content:center; align-items:center; gap:.7rem; flex-wrap:wrap; margin:.25rem 0 .45rem; }
    .exam-group-slime { width:38px; height:30px; border-radius:50% 50% 42% 42%/62% 62% 38% 38%; background:#e3eee7; border:1px solid #d1e1d7; position:relative; opacity:.62; }
    .exam-group-slime.done { background:linear-gradient(145deg,#84e5a3,#43c879); opacity:1; }
    .exam-group-slime.current { background:linear-gradient(145deg,#9af0b3,#35c878); border-color:#31bd70; opacity:1; transform:scale(1.15); box-shadow:0 0 0 4px rgba(49,201,120,.12); }
    .exam-group-slime:before,.exam-group-slime:after { content:""; position:absolute; top:40%; width:4px; height:6px; border-radius:50%; background:#173b2b; }
    .exam-group-slime:before { left:29%; }
    .exam-group-slime:after { right:29%; }
    .exam-progress-label { text-align:center; color:#688476; font-size:.85rem; font-weight:800; margin:.35rem 0 .1rem; }
    [class*="st-key-exam_year_"] button { min-height:68px !important; font-size:1.02rem !important; }
    [class*="st-key-exam_subject_"] button { min-height:70px !important; white-space:normal !important; line-height:1.4 !important; }
'''

new_css = '''    .exam-round-chip { width:max-content; margin:1rem auto .45rem; padding:.28rem .78rem; border-radius:999px; background:#eaf9ef; border:1px solid #cde8d7; color:#278657; font-size:.84rem; font-weight:900; letter-spacing:.03em; }
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
'''
replace_once(old_css, new_css, "exam progress CSS")

# Smaller group slimes on mobile; keep 8 (or more) on one row.
replace_once(
    '        .slime-track { grid-template-columns:repeat(10, minmax(19px, 30px)); gap:.22rem; padding:.4rem 0 1rem; }\n',
    '''        .slime-track { grid-template-columns:repeat(10, minmax(19px, 30px)); gap:.22rem; padding:.4rem 0 1rem; }\n        [class*="st-key-exam_group_nav"] [data-testid="stHorizontalBlock"],\n        [class*="st-key-exam_small_nav"] [data-testid="stHorizontalBlock"] { gap:.14rem !important; }\n        [class*="st-key-exam_group_nav"] [data-testid="stColumn"] { flex-basis:28px !important; width:28px !important; }\n        [class*="st-key-exam_small_nav"] [data-testid="stColumn"] { flex-basis:23px !important; width:23px !important; }\n        [class*="st-key-exam_group_"] button { width:27px !important; height:21px !important; min-width:27px !important; min-height:21px !important; }\n        [class*="st-key-exam_small_"] button { width:21px !important; height:17px !important; min-width:21px !important; min-height:17px !important; }\n        [class*="st-key-exam_group_"] button::before,[class*="st-key-exam_group_"] button::after { width:3px; height:4px; }\n        [class*="st-key-exam_small_"] button::before,[class*="st-key-exam_small_"] button::after { width:2px; height:3px; }\n        [class*="st-key-exam_group_"] button p { font-size:.52rem !important; }\n        [class*="st-key-exam_small_"] button p { font-size:.42rem !important; }\n''',
    "mobile exam slime sizing",
)

start = text.index("def national_exam_home():")
end = text.index("\ndef save_current_national_exam_state", start)

new_exam_ui = r'''def _queue_national_exam_choice(widget_key, exam_round):
    subject = st.session_state.get(widget_key)
    if subject and subject != "請選擇科目":
        st.session_state.national_exam_pending_choice = (subject, exam_round)


def national_exam_home():
    topbar()
    st.markdown('<div class="study-header"><div class="eyebrow">NATIONAL EXAM</div><div class="hero-title" style="font-size:2.05rem">我要刷國考</div><div class="hero-copy">先選年份，再選科目；選好科目後直接開始第 1 題。</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title" style="margin-top:.9rem">① 選擇年份</div>', unsafe_allow_html=True)
    years = NATIONAL_EXAM_YEARS
    current_year = int(st.session_state.national_exam_year)
    selected_year = st.selectbox(
        "年份",
        years,
        index=years.index(current_year) if current_year in years else 0,
        format_func=roc_year_label,
        key="national_exam_year_select",
        label_visibility="collapsed",
    )
    if selected_year != current_year:
        st.session_state.national_exam_year = selected_year
        st.session_state.national_exam_load_error = None
        st.session_state.national_exam_pending_choice = None

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

    version = int(st.session_state.national_exam_picker_version)
    for exam_round in NATIONAL_EXAM_ROUNDS:
        subjects = [item["subject"] for item in entries if item["exam_round"] == exam_round]
        if not subjects:
            continue
        st.markdown(f'<div class="exam-round-chip">{exam_round}</div>', unsafe_allow_html=True)
        widget_key = f"national_exam_subject_select_{selected_year}_{exam_round}_{version}"
        st.selectbox(
            f"{exam_round}科目",
            ["請選擇科目"] + subjects,
            index=0,
            key=widget_key,
            label_visibility="collapsed",
            on_change=_queue_national_exam_choice,
            args=(widget_key, exam_round),
        )

    pending = st.session_state.national_exam_pending_choice
    if pending:
        st.session_state.national_exam_pending_choice = None
        subject, exam_round = pending
        with st.spinner("正在載入國考題目…"):
            try:
                usable, excluded, total = load_national_exam_paper(selected_year, exam_round, subject)
            except Exception as error:
                st.session_state.national_exam_load_error = f"{type(error).__name__}: {error}"
                usable = []
                excluded = []
                total = 0
        if usable:
            start_national_exam_quiz(usable, selected_year, exam_round, subject, excluded, total)
        elif not st.session_state.national_exam_load_error:
            st.session_state.national_exam_load_error = "這份試卷目前沒有可直接作答的題目。"

    if st.session_state.national_exam_load_error:
        st.error(st.session_state.national_exam_load_error)


def render_national_exam_progress(current_index, question_count):
    answers = st.session_state.national_exam_answers
    group_size = 10
    current_group = current_index // group_size
    group_count = (question_count + group_size - 1) // group_size

    with st.container(key="exam_group_nav"):
        group_cols = st.columns(group_count)
        for group, col in enumerate(group_cols):
            start = group * group_size
            end = min(start + group_size, question_count)
            if group == current_group:
                state = "current"
            elif all(i in answers for i in range(start, end)):
                state = "done"
            else:
                state = "future"
            with col:
                if st.button(
                    "⌣",
                    key=f"exam_group_{state}_{group}_{current_index}",
                    help=f"跳到第 {start + 1}–{end} 題",
                ):
                    st.session_state.national_exam_index = start
                    st.rerun()

    start = current_group * group_size
    end = min(start + group_size, question_count)
    st.markdown(f'<div class="exam-progress-label">目前區段：第 {start + 1}–{end} 題</div>', unsafe_allow_html=True)

    with st.container(key="exam_small_nav"):
        small_cols = st.columns(end - start)
        for offset, col in enumerate(small_cols):
            question_index = start + offset
            if question_index == current_index:
                state = "current"
            elif question_index in answers:
                state = "done"
            else:
                state = "future"
            with col:
                if st.button(
                    "⌣",
                    key=f"exam_small_{state}_{question_index}_{current_index}",
                    help=f"跳到第 {question_index + 1} 題",
                ):
                    st.session_state.national_exam_index = question_index
                    st.rerun()

'''

text = text[:start] + new_exam_ui + text[end:]

replace_once(
    '    st.markdown(national_exam_progress_markup(index, len(questions)), unsafe_allow_html=True)\n',
    '    render_national_exam_progress(index, len(questions))\n',
    "render clickable national exam progress",
)

path.write_text(text, encoding="utf-8")
print("National exam UI refined")
