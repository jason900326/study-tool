from pathlib import Path

path = Path("streamlit_app.py")
text = path.read_text(encoding="utf-8")


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly 1 match, got {count}")
    text = text.replace(old, new, 1)


# 1) Remove the fake HTML wrapper around the Streamlit file uploader.
# Streamlit widgets cannot actually be nested inside a markdown <div>, so the
# opening tag rendered as a separate empty white card.
replace_once(
    '''    st.markdown('<div class="upload-shell">', unsafe_allow_html=True)\n    uploaded = st.file_uploader("選擇 PDF 教材", type=["pdf"], key="medslime_material_pdf")\n    st.markdown("</div>", unsafe_allow_html=True)''',
    '''    uploaded = st.file_uploader("選擇 PDF 教材", type=["pdf"], key="medslime_material_pdf")''',
    "remove uploader wrapper",
)

# 2) Replace linear progress-bar CSS with ten small slime indicators.
replace_once(
    '''    .quiz-topline { display:flex; justify-content:space-between; align-items:center; gap:1rem; margin:.8rem 0 .55rem; }\n    .quiz-count { color:#2b6850; font-weight:900; }\n    .quiz-subject { color:#789083; font-size:.9rem; }\n    .quiz-progress { width:100%; height:9px; border-radius:999px; background:#dce9df; overflow:hidden; margin-bottom:1.15rem; }\n    .quiz-progress-fill { height:100%; background:linear-gradient(90deg,#57d188,#42bfa5); transition:width .25s ease; }''',
    '''    .quiz-topline { display:flex; align-items:center; margin:.8rem 0 .5rem; }\n    .quiz-count { color:#2b6850; font-weight:900; }\n    .slime-track {\n        display:grid;\n        grid-template-columns:repeat(10, minmax(22px, 38px));\n        justify-content:space-between;\n        align-items:center;\n        gap:.35rem;\n        width:100%;\n        padding:.45rem .2rem 1.15rem;\n    }\n    .mini-progress-slime {\n        width:100%;\n        max-width:38px;\n        aspect-ratio:1.28 / 1;\n        position:relative;\n        border-radius:50% 50% 42% 42% / 62% 62% 38% 38%;\n        background:#e4eee8;\n        border:1px solid #d3e2d9;\n        transition:transform .18s ease, opacity .18s ease, box-shadow .18s ease;\n    }\n    .mini-progress-slime.done {\n        background:linear-gradient(145deg,#8be8a8,#43c879);\n        border-color:#75d998;\n    }\n    .mini-progress-slime.current {\n        background:linear-gradient(145deg,#9af0b3,#35c878);\n        border-color:#31bd70;\n        transform:scale(1.14);\n        box-shadow:0 0 0 4px rgba(49,201,120,.14), 0 5px 12px rgba(35,139,78,.14);\n        animation:progressSlime .75s ease-out both;\n    }\n    .mini-progress-slime.future { opacity:.62; }\n    .mini-progress-slime::before,\n    .mini-progress-slime::after {\n        content:\"\";\n        position:absolute;\n        top:39%;\n        width:10%;\n        min-width:2px;\n        aspect-ratio:1 / 1.35;\n        border-radius:50%;\n        background:#173b2b;\n    }\n    .mini-progress-slime::before { left:30%; }\n    .mini-progress-slime::after { right:30%; }\n    .mini-progress-slime.future::before,\n    .mini-progress-slime.future::after { opacity:.28; }\n    .mini-progress-mouth {\n        position:absolute;\n        left:40%;\n        top:60%;\n        width:20%;\n        height:8%;\n        border-bottom:1.5px solid #173b2b;\n        border-radius:0 0 50% 50%;\n        opacity:.85;\n    }\n    .mini-progress-slime.future .mini-progress-mouth { opacity:.22; }''',
    "replace progress CSS",
)

replace_once(
    '''    @keyframes dots { 0%,70%,100% { opacity:.28; transform:translateY(0); } 35% { opacity:1; transform:translateY(-3px); } }''',
    '''    @keyframes dots { 0%,70%,100% { opacity:.28; transform:translateY(0); } 35% { opacity:1; transform:translateY(-3px); } }\n    @keyframes progressSlime { 0% { transform:scale(.94); } 65% { transform:scale(1.19); } 100% { transform:scale(1.14); } }''',
    "add progress animation",
)

# The wrapper no longer exists; keep the dropzone styling only.
replace_once(
    '''    .upload-shell { background:rgba(255,255,255,.92); border:1px solid #dceae2; border-radius:27px; padding:1.1rem 1.15rem 1.2rem; box-shadow:0 12px 30px rgba(30,78,50,.05); }\n''',
    '''''',
    "remove upload shell CSS",
)
text = text.replace(
    '.home-copy-card,.home-slime-card,.home-task,.choice-card,.study-header,.intro-panel,.upload-shell { animation:pageIn .20s ease-out both; }',
    '.home-copy-card,.home-slime-card,.home-task,.choice-card,.study-header,.intro-panel { animation:pageIn .20s ease-out both; }',
)

# Mobile slimes stay compact and fit all ten on one row.
replace_once(
    '''        .quiz-card { padding:1.2rem 1.1rem; }\n        .quiz-question { font-size:1.08rem; }\n        .quiz-topline { align-items:flex-start; }''',
    '''        .quiz-card { padding:1.2rem 1.1rem; }\n        .quiz-question { font-size:1.08rem; }\n        .slime-track { grid-template-columns:repeat(10, minmax(19px, 30px)); gap:.22rem; padding:.4rem 0 1rem; }''',
    "mobile slime progress",
)

# 3) Add a helper for the ten-slime progress indicator and a true Streamlit dialog.
marker = '''def unanswered_numbers(question_count):\n    return [number + 1 for number in range(question_count) if number not in st.session_state.quiz_answers]\n\n\ndef material_quiz_page():'''
replacement = '''def unanswered_numbers(question_count):\n    return [number + 1 for number in range(question_count) if number not in st.session_state.quiz_answers]\n\n\ndef slime_progress_markup(current_index, question_count):\n    slimes = []\n    for number in range(question_count):\n        if number == current_index:\n            state = "current"\n        elif number in st.session_state.quiz_answers:\n            state = "done"\n        else:\n            state = "future"\n        slimes.append(\n            f'<div class="mini-progress-slime {state}" title="第 {number + 1} 題">'\n            '<span class="mini-progress-mouth"></span></div>'\n        )\n    return '<div class="slime-track">' + "".join(slimes) + '</div>'\n\n\ndef show_finish_confirmation(missing):\n    @st.dialog("要提前結束測驗嗎？")\n    def _finish_dialog():\n        missing_text = "、".join(map(str, missing))\n        st.write(f"還有未作答題目：{missing_text}")\n        st.caption("你可以回去補答，也可以直接結束這次測驗。")\n        left, right = st.columns(2)\n        with left:\n            if st.button("繼續作答", use_container_width=True, key="dialog_continue_quiz"):\n                st.rerun()\n        with right:\n            if st.button("仍要結束測驗", type="primary", use_container_width=True, key="dialog_force_finish"):\n                st.session_state.quiz_finished = True\n                st.session_state.quiz_finish_pending = False\n                st.session_state.medslime_page = "quiz_result"\n                st.session_state.menu_open = False\n                st.rerun()\n    _finish_dialog()\n\n\ndef material_quiz_page():'''
replace_once(marker, replacement, "insert slime helper and dialog")

# 4) Simplify quiz header: count only, no AI subject or filename.
replace_once(
    '''    safe_question = html.escape(str(question["question"]))\n    safe_subject = html.escape(str(st.session_state.material_subject or "教材測驗"))\n    safe_filename = html.escape(str(st.session_state.uploaded_learning_file or ""))\n\n    st.markdown('<div class="quiz-stage">', unsafe_allow_html=True)\n    st.markdown(f'<div class="quiz-topline"><div><span class="quiz-count">第 {index + 1} / {len(questions)} 題</span><div class="quiz-subject">{safe_subject}</div></div><div class="muted">{safe_filename}</div></div>', unsafe_allow_html=True)\n    progress = int(((index + 1) / len(questions)) * 100)\n    st.markdown(f'<div class="quiz-progress"><div class="quiz-progress-fill" style="width:{progress}%"></div></div>', unsafe_allow_html=True)''',
    '''    safe_question = html.escape(str(question["question"]))\n\n    st.markdown('<div class="quiz-stage">', unsafe_allow_html=True)\n    st.markdown(f'<div class="quiz-topline"><span class="quiz-count">第 {index + 1} / {len(questions)} 題</span></div>', unsafe_allow_html=True)\n    st.markdown(slime_progress_markup(index, len(questions)), unsafe_allow_html=True)''',
    "simplify quiz heading and use slime progress",
)

# 5) Use a real modal dialog for unfinished questions instead of inline warning card.
replace_once(
    '''            if missing:\n                st.session_state.quiz_finish_pending = True\n                st.rerun()\n            else:\n                st.session_state.quiz_finished = True\n                goto("quiz_result")\n\n    if st.session_state.quiz_finish_pending:\n        missing = unanswered_numbers(len(questions))\n        if missing:\n            st.markdown(f'<div class="finish-warning">還有未作答題目：{html.escape("、".join(map(str, missing)))}。你可以回去補答，也可以直接結束這次測驗。</div>', unsafe_allow_html=True)\n            c1, c2 = st.columns(2)\n            with c1:\n                if st.button("繼續作答", use_container_width=True, key="continue_quiz"):\n                    st.session_state.quiz_finish_pending = False\n                    st.rerun()\n            with c2:\n                if st.button("仍要結束測驗", type="primary", use_container_width=True, key="force_finish_quiz"):\n                    st.session_state.quiz_finish_pending = False\n                    st.session_state.quiz_finished = True\n                    goto("quiz_result")\n        else:\n            st.session_state.quiz_finish_pending = False\n            st.session_state.quiz_finished = True\n            goto("quiz_result")''',
    '''            if missing:\n                show_finish_confirmation(missing)\n            else:\n                st.session_state.quiz_finished = True\n                goto("quiz_result")''',
    "replace inline finish confirmation with dialog",
)

# The old warning style is now unused.
text = text.replace(
    '    .finish-warning { background:#fff9d9; border:1px solid #eddc75; border-radius:16px; padding:.85rem 1rem; margin:.85rem 0 .6rem; color:#5d5327; line-height:1.6; font-weight:700; }\n\n',
    '',
)

path.write_text(text, encoding="utf-8")
print("Patched streamlit_app.py successfully")
