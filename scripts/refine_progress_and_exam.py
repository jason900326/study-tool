from pathlib import Path

path = Path("streamlit_app.py")
text = path.read_text(encoding="utf-8")


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, got {count}")
    text = text.replace(old, new, 1)


# 1) Put the uploader inside the same visual card and clean up its CTA text.
replace_once(
    '''    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] { border:none !important; background:transparent !important; padding:0 !important; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzoneInstructions"],\n    [class*="st-key-material_intro_uploader"] small { display:none !important; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button { width:100% !important; min-height:48px !important; background:#31c978 !important; color:white !important; border:1px solid #31c978 !important; border-radius:15px !important; font-size:0 !important; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button::after { content:"☁️ 上傳教材開始學習"; font-size:.95rem; font-weight:850; }\n''',
    '''    [class*="st-key-material_intro_card"] { max-width:840px; margin:.3rem auto 1.15rem; background:rgba(255,255,255,.76); border:1px solid #dfebe4; border-radius:30px; padding:2rem 2rem 1.75rem; box-shadow:0 16px 38px rgba(30,82,51,.055); text-align:center; }\n    [class*="st-key-material_intro_uploader"] { margin-top:1.15rem; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] { border:none !important; background:transparent !important; padding:0 !important; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzoneInstructions"],\n    [class*="st-key-material_intro_uploader"] small { display:none !important; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button { width:100% !important; min-height:48px !important; background:#31c978 !important; color:white !important; border:1px solid #31c978 !important; border-radius:15px !important; font-size:0 !important; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button p,\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button span { font-size:0 !important; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button::after { content:"☁️ 上傳教材開始學習"; font-size:.95rem; font-weight:850; }\n''',
    "material intro card CSS",
)

# 2) Shared clickable material progress + four explicit status colors.
needle = '''    [class*="st-key-exam_group_current_uncertain"] button,\n    [class*="st-key-exam_small_current_uncertain"] button {\n        background:linear-gradient(145deg,#ffe98f,#f4c94f) !important;\n        border-color:#d8ac2d !important;\n        box-shadow:0 0 0 3px rgba(240,190,55,.18) !important;\n    }\n'''
addition = needle + '''    /* Unified question-state colors: gray untouched, red uncertain only, yellow uncertain+answer, green answered. */\n    [class*="st-key-exam_group_gray_"] button,[class*="st-key-exam_small_gray_"] button,\n    [class*="st-key-exam_group_current_gray_"] button,[class*="st-key-exam_small_current_gray_"] button { background:#e3eee7 !important; border-color:#d1e1d7 !important; opacity:.62 !important; }\n    [class*="st-key-exam_group_red_"] button,[class*="st-key-exam_small_red_"] button,\n    [class*="st-key-exam_group_current_red_"] button,[class*="st-key-exam_small_current_red_"] button { background:linear-gradient(145deg,#ffaaa8,#ef6b69) !important; border-color:#e36361 !important; opacity:1 !important; }\n    [class*="st-key-exam_group_yellow_"] button,[class*="st-key-exam_small_yellow_"] button,\n    [class*="st-key-exam_group_current_yellow_"] button,[class*="st-key-exam_small_current_yellow_"] button { background:linear-gradient(145deg,#ffe98f,#f4c94f) !important; border-color:#e2b83d !important; opacity:1 !important; }\n    [class*="st-key-exam_group_green_"] button,[class*="st-key-exam_small_green_"] button,\n    [class*="st-key-exam_group_current_green_"] button,[class*="st-key-exam_small_current_green_"] button { background:linear-gradient(145deg,#84e5a3,#43c879) !important; border-color:#6fd391 !important; opacity:1 !important; }\n    [class*="st-key-exam_group_current_"] button,[class*="st-key-exam_small_current_"] button { box-shadow:0 0 0 3px rgba(49,201,120,.15) !important; transform:scale(1.08) !important; }\n\n    [class*="st-key-material_small_nav"] [data-testid="stHorizontalBlock"] { flex-wrap:nowrap !important; justify-content:center !important; align-items:center !important; gap:.35rem !important; }\n    [class*="st-key-material_small_nav"] [data-testid="stColumn"] { flex:0 1 38px !important; width:38px !important; min-width:0 !important; }\n    [class*="st-key-material_small_"] button { width:34px !important; height:27px !important; min-width:34px !important; min-height:27px !important; margin:0 auto !important; padding:0 !important; position:relative !important; border-radius:50% 50% 42% 42% / 62% 62% 38% 38% !important; border:1px solid #d1e1d7 !important; color:#173b2b !important; box-shadow:none !important; transform:none !important; }\n    [class*="st-key-material_small_"] button::before,[class*="st-key-material_small_"] button::after { content:""; position:absolute; top:38%; width:4px; height:6px; border-radius:50%; background:#173b2b; }\n    [class*="st-key-material_small_"] button::before { left:28%; }\n    [class*="st-key-material_small_"] button::after { right:28%; }\n    [class*="st-key-material_small_"] button p { position:absolute !important; left:50% !important; top:48% !important; transform:translateX(-50%) !important; margin:0 !important; line-height:1 !important; font-size:.6rem !important; }\n    [class*="st-key-material_small_gray_"] button,[class*="st-key-material_small_current_gray_"] button { background:#e4eee8 !important; border-color:#d3e2d9 !important; opacity:.62 !important; }\n    [class*="st-key-material_small_red_"] button,[class*="st-key-material_small_current_red_"] button { background:linear-gradient(145deg,#ffaaa8,#ef6b69) !important; border-color:#e36361 !important; opacity:1 !important; }\n    [class*="st-key-material_small_yellow_"] button,[class*="st-key-material_small_current_yellow_"] button { background:linear-gradient(145deg,#ffe98f,#f4c94f) !important; border-color:#e2b83d !important; opacity:1 !important; }\n    [class*="st-key-material_small_green_"] button,[class*="st-key-material_small_current_green_"] button { background:linear-gradient(145deg,#8be8a8,#43c879) !important; border-color:#75d998 !important; opacity:1 !important; }\n    [class*="st-key-material_small_current_"] button { box-shadow:0 0 0 4px rgba(49,201,120,.14),0 5px 12px rgba(35,139,78,.12) !important; transform:scale(1.12) !important; }\n'''
replace_once(needle, addition, "progress state CSS")

# Keep all ten material slimes on one line on mobile.
replace_once(
    '''        [class*="st-key-exam_small_"] button p { font-size:.42rem !important; }\n''',
    '''        [class*="st-key-exam_small_"] button p { font-size:.42rem !important; }\n        [class*="st-key-material_small_nav"] [data-testid="stHorizontalBlock"] { gap:.16rem !important; }\n        [class*="st-key-material_small_nav"] [data-testid="stColumn"] { flex-basis:25px !important; width:25px !important; }\n        [class*="st-key-material_small_"] button { width:23px !important; height:18px !important; min-width:23px !important; min-height:18px !important; }\n        [class*="st-key-material_small_"] button::before,[class*="st-key-material_small_"] button::after { width:2px; height:3px; }\n        [class*="st-key-material_small_"] button p { font-size:.42rem !important; }\n''',
    "mobile material slime sizing",
)

# 3) Remove the visible '考次' label; keep only the two buttons between year and subject.
replace_once(
    '''        selected_round = st.radio(\n            "考次",\n            NATIONAL_EXAM_ROUNDS,\n            horizontal=True,\n            key="national_exam_round_select",\n        )\n''',
    '''        selected_round = st.radio(\n            "考次",\n            NATIONAL_EXAM_ROUNDS,\n            horizontal=True,\n            key="national_exam_round_select",\n            label_visibility="collapsed",\n        )\n''',
    "hide exam round label",
)

# 4) National exam progress state: red/yellow/green/gray and immediate widget-state awareness.
start = text.index("def render_national_exam_progress(")
end = text.index("\ndef save_current_national_exam_state", start)
new_exam_progress = r'''def _national_question_progress_state(question_index):
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

'''
text = text[:start] + new_exam_progress + text[end:]

# 5) Official source link on every national-exam question page.
replace_once(
    '''    st.markdown(f'<div class="quiz-card">{official}<div class="quiz-question" style="margin-top:.25rem">{html.escape(str(question["question"]))}</div></div>', unsafe_allow_html=True)\n\n    answer_key = f"exam_answer_{index}"\n''',
    '''    st.markdown(f'<div class="quiz-card">{official}<div class="quiz-question" style="margin-top:.25rem">{html.escape(str(question["question"]))}</div></div>', unsafe_allow_html=True)\n    if question.get("source_url"):\n        st.link_button("查看官方原題 ↗", question["source_url"])\n\n    answer_key = f"exam_answer_{index}"\n''',
    "national exam source link",
)

# 6) Material intro: uploader is physically inside the same keyed Streamlit card.
start = text.index("def study_material_intro():")
end = text.index("\ndef study_material_upload():", start)
old_intro = text[start:end]
if 'with st.container(key="material_intro_card")' in old_intro:
    raise RuntimeError("material intro already refined")
body_start = old_intro.index("    st.markdown('<div class=\"intro-panel\"")
body_end = old_intro.index("\n\n    if uploaded is None:")
new_top = r'''    with st.container(key="material_intro_card"):
        st.markdown('<div class="intro-art"><div class="mini-slime"><div class="mini-shine"></div><div class="mini-mouth"></div></div><div class="book-stack">📚</div></div><div class="hero-title" style="font-size:2rem">上傳教材，AI 直接生成 10 題<br>開始你的專屬測驗。</div><div class="hero-copy" style="max-width:680px;margin:.8rem auto 0">選好 PDF 後，MedSlime 會直接讀取教材；完成後自動帶你進入第 1 題。</div>', unsafe_allow_html=True)
        with st.container(key="material_intro_uploader"):
            uploaded = st.file_uploader("上傳教材開始學習", type=["pdf"], key="medslime_material_pdf_intro", label_visibility="collapsed")
'''
old_intro = old_intro[:body_start] + new_top + old_intro[body_end:]
text = text[:start] + old_intro + text[end:]

# 7) Replace non-clickable material HTML slimes with real buttons and four states.
start = text.index("def slime_progress_markup(")
end = text.index("\n\ndef review_options_markup", start)
new_material_progress = r'''def _material_question_progress_state(question_index):
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
'''
text = text[:start] + new_material_progress + text[end:]

replace_once(
    '    st.markdown(slime_progress_markup(index, len(questions)), unsafe_allow_html=True)\n',
    '    render_material_progress(index, len(questions))\n',
    "render clickable material progress",
)

path.write_text(text, encoding="utf-8")
print("refined material upload, progress states, and national exam source links")
