from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 match, got {count}')
    text = text.replace(old, new, 1)


# ---------- CSS ----------
replace_once(
    '    .exam-round-chip { width:max-content; margin:1rem auto .45rem; padding:.28rem .78rem; border-radius:999px; background:#eaf9ef; border:1px solid #cde8d7; color:#278657; font-size:.84rem; font-weight:900; letter-spacing:.03em; }\n',
    '''    .exam-round-chip { width:max-content; margin:1rem auto .45rem; padding:.28rem .78rem; border-radius:999px; background:#eaf9ef; border:1px solid #cde8d7; color:#278657; font-size:.84rem; font-weight:900; letter-spacing:.03em; }\n    [class*="st-key-exam_config_card"] { background:rgba(255,255,255,.92); border:1px solid #dceae2; border-radius:26px; padding:1.2rem 1.25rem 1.35rem; box-shadow:0 12px 30px rgba(31,83,53,.055); }\n    [class*="st-key-exam_config_card"] [data-baseweb="select"] > div { background:#ffffff !important; color:#244c39 !important; border-color:#d8e8df !important; }\n    [class*="st-key-exam_config_card"] [data-baseweb="select"] span { color:#244c39 !important; }\n    [class*="st-key-national_exam_round_select"] [role="radiogroup"] { justify-content:center !important; gap:.65rem !important; }\n    [class*="st-key-national_exam_round_select"] label { background:#f5faf7; border:1px solid #d8e8df; border-radius:999px; padding:.45rem .9rem; }\n    [class*="st-key-national_exam_round_select"] label:has(input:checked) { background:#e8f8ee; border-color:#92d8ad; }\n''',
    'exam config CSS',
)

replace_once(
    '    [class*="st-key-exam_group_future_"] button,\n    [class*="st-key-exam_small_future_"] button { opacity:.55 !important; }\n',
    '''    [class*="st-key-exam_group_future_"] button,\n    [class*="st-key-exam_small_future_"] button { opacity:.55 !important; }\n    [class*="st-key-exam_group_uncertain"] button,\n    [class*="st-key-exam_small_uncertain"] button {\n        background:linear-gradient(145deg,#ffe98f,#f4c94f) !important;\n        border-color:#e8bd40 !important;\n        opacity:1 !important;\n    }\n    [class*="st-key-exam_group_current_uncertain"] button,\n    [class*="st-key-exam_small_current_uncertain"] button {\n        background:linear-gradient(145deg,#ffe98f,#f4c94f) !important;\n        border-color:#d8ac2d !important;\n        box-shadow:0 0 0 3px rgba(240,190,55,.18) !important;\n    }\n''',
    'yellow exam progress CSS',
)

replace_once(
    '    .mini-progress-slime.future .mini-progress-mouth { opacity:.22; }\n',
    '''    .mini-progress-slime.future .mini-progress-mouth { opacity:.22; }\n    .mini-progress-slime.uncertain { background:linear-gradient(145deg,#ffe98f,#f4c94f); border-color:#e4bb43; opacity:1; }\n    .mini-progress-slime.uncertain.current { box-shadow:0 0 0 4px rgba(240,190,55,.18),0 5px 12px rgba(183,135,25,.12); }\n''',
    'yellow material progress CSS',
)

replace_once(
    '    .result-card { background:rgba(255,255,255,.96); border:1px solid #dceae2; border-radius:25px; padding:1.3rem 1.4rem; margin:.8rem 0; animation:pageIn .2s ease-out both; }\n',
    '''    .result-card { background:rgba(255,255,255,.96); border:1px solid #dceae2; border-radius:25px; padding:1.3rem 1.4rem; margin:.8rem 0; animation:pageIn .2s ease-out both; }\n    .review-options { display:grid; gap:.48rem; margin-top:.9rem; }\n    .review-option { padding:.7rem .85rem; border-radius:12px; border:1px solid #e1ebe5; background:#fbfdfc; color:#244c39; line-height:1.5; }\n    .review-option.correct { background:#e9f9ef; border-color:#b8e5c9; }\n    .review-option.wrong { background:#fdecec; border-color:#f3c2c2; }\n    .review-option-letter { display:inline-flex; width:1.55rem; height:1.55rem; align-items:center; justify-content:center; border-radius:50%; background:rgba(255,255,255,.78); margin-right:.55rem; font-weight:900; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] { border:none !important; background:transparent !important; padding:0 !important; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzoneInstructions"],\n    [class*="st-key-material_intro_uploader"] small { display:none !important; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button { width:100% !important; min-height:48px !important; background:#31c978 !important; color:white !important; border:1px solid #31c978 !important; border-radius:15px !important; font-size:0 !important; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button::after { content:"☁️ 上傳教材開始學習"; font-size:.95rem; font-weight:850; }\n''',
    'review + uploader CSS',
)

# ---------- National exam selector card ----------
start = text.index('def national_exam_home():')
end = text.index('\ndef render_national_exam_progress', start)
new_home = r'''def national_exam_home():
    topbar()
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

'''
text = text[:start] + new_home + text[end:]

# ---------- Clickable progress with uncertain state ----------
start = text.index('def render_national_exam_progress(')
end = text.index('\ndef save_current_national_exam_state', start)
new_progress = r'''def render_national_exam_progress(current_index, question_count):
    answers = st.session_state.national_exam_answers
    uncertain = st.session_state.national_exam_uncertain
    group_size = 10
    current_group = current_index // group_size
    group_count = (question_count + group_size - 1) // group_size

    with st.container(key="exam_group_nav"):
        group_cols = st.columns(group_count)
        for group, col in enumerate(group_cols):
            start = group * group_size
            end = min(start + group_size, question_count)
            completed = all(i in answers for i in range(start, end))
            has_uncertain = any(i in answers and uncertain.get(i, False) for i in range(start, end))
            current_uncertain = group == current_group and current_index in answers and uncertain.get(current_index, False)
            if current_uncertain:
                state = "current_uncertain"
            elif group == current_group:
                state = "current"
            elif completed and has_uncertain:
                state = "uncertain"
            elif completed:
                state = "done"
            else:
                state = "future"
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
            answered = question_index in answers
            is_uncertain = answered and uncertain.get(question_index, False)
            if question_index == current_index and is_uncertain:
                state = "current_uncertain"
            elif question_index == current_index:
                state = "current"
            elif is_uncertain:
                state = "uncertain"
            elif answered:
                state = "done"
            else:
                state = "future"
            with col:
                if st.button("⌣", key=f"exam_small_{state}_{question_index}_{current_index}", help=f"跳到第 {question_index + 1} 題"):
                    st.session_state.national_exam_index = question_index
                    st.rerun()

'''
text = text[:start] + new_progress + text[end:]

# ---------- Material slime progress uncertain ----------
old = '''def slime_progress_markup(current_index, question_count):\n    slimes = []\n    for number in range(question_count):\n        if number == current_index:\n            state = "current"\n        elif number in st.session_state.quiz_answers:\n            state = "done"\n        else:\n            state = "future"\n        slimes.append(\n            f'<div class="mini-progress-slime {state}" title="第 {number + 1} 題">'\n            '<span class="mini-progress-mouth"></span></div>'\n        )\n    return '<div class="slime-track">' + "".join(slimes) + '</div>'\n'''
new = '''def slime_progress_markup(current_index, question_count):\n    slimes = []\n    for number in range(question_count):\n        answered = number in st.session_state.quiz_answers\n        uncertain = answered and bool(st.session_state.quiz_uncertain.get(number, False))\n        if number == current_index and uncertain:\n            state = "uncertain current"\n        elif number == current_index:\n            state = "current"\n        elif uncertain:\n            state = "uncertain"\n        elif answered:\n            state = "done"\n        else:\n            state = "future"\n        slimes.append(\n            f'<div class="mini-progress-slime {state}" title="第 {number + 1} 題">'\n            '<span class="mini-progress-mouth"></span></div>'\n        )\n    return '<div class="slime-track">' + "".join(slimes) + '</div>'\n'''
replace_once(old, new, 'material uncertain progress')

# ---------- Shared review option renderer ----------
marker = '\ndef show_finish_confirmation(missing):\n'
helper = r'''

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
            f'<div class="{cls}"><span class="review-option-letter">{letters[idx] if idx < 4 else idx + 1}</span>{html.escape(str(option))}</div>'
        )
    return '<div class="review-options">' + ''.join(rows) + '</div>'

'''
if marker not in text:
    raise RuntimeError('review helper marker not found')
text = text.replace(marker, helper + marker, 1)

# ---------- Direct upload on intro page ----------
start = text.index('def study_material_intro():')
end = text.index('\ndef study_material_upload():', start)
new_intro = r'''def study_material_intro():
    topbar()
    if st.button("← 返回學習", key="intro_back"):
        goto("study")
    st.markdown('<div class="intro-panel"><div class="intro-art"><div class="mini-slime"><div class="mini-shine"></div><div class="mini-mouth"></div></div><div class="book-stack">📚</div></div><div class="hero-title" style="font-size:2rem">上傳教材，AI 直接生成 10 題<br>開始你的專屬測驗。</div><div class="hero-copy" style="max-width:680px;margin:.8rem auto 0">選好 PDF 後，MedSlime 會直接讀取教材；完成後自動帶你進入第 1 題。</div></div>', unsafe_allow_html=True)

    with st.container(key="material_intro_uploader"):
        uploaded = st.file_uploader("上傳教材開始學習", type=["pdf"], key="medslime_material_pdf_intro", label_visibility="collapsed")

    if uploaded is None:
        if st.session_state.material_generation_error:
            st.error(st.session_state.material_generation_error)
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

'''
text = text[:start] + new_intro + text[end:]

# ---------- Material result: full options + highlights ----------
start = text.index('def material_quiz_result():')
end = text.index('\n\n# =========================================================\n# Other MVP pages', start)
new_material_result = r'''def material_quiz_result():
    questions = st.session_state.material_questions or []
    if len(questions) != QUIZ_SIZE:
        goto("study_material_intro")

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
            tag = "答對，但不確定" if is_correct and uncertain else "需要訂正"
            st.markdown(
                f'<div class="result-card"><div class="eyebrow">Q{index + 1} · {tag}</div><div class="card-title" style="margin-top:.35rem">{html.escape(str(question["question"]))}</div>{review_options_markup(question, answer)}</div>',
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
'''
text = text[:start] + new_material_result + text[end:]

# ---------- National exam result: full options + future explanation hook ----------
start = text.index('def national_exam_result_page():')
end = text.index('\ndef study_material_intro():', start)
new_exam_result = r'''def national_exam_result_page():
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
            tag = "答對，但不確定" if is_correct and uncertain else "需要訂正"
            official = question.get("official_question_number", index + 1)
            st.markdown(
                f'<div class="result-card"><div class="eyebrow">官方第 {official} 題 · {tag}</div><div class="card-title" style="margin-top:.35rem">{html.escape(str(question["question"]))}</div>{review_options_markup(question, answer)}</div>',
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

'''
text = text[:start] + new_exam_result + text[end:]

path.write_text(text, encoding='utf-8')
