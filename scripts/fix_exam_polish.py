from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 match, got {count}')
    text = text.replace(old, new, 1)


# 1) Scientific notation normalization helper.
replace_once(
    'import random\nfrom io import BytesIO\n',
    'import random\nimport re\nfrom io import BytesIO\n',
    'import re',
)

replace_once(
    'QUIZ_SIZE = 10\n\nDEFAULT_STATE = {\n',
    '''QUIZ_SIZE = 10\n\n_SUPERSCRIPT_MAP = str.maketrans("+-0123456789", "⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹")\n\n\ndef _to_superscript(value):\n    return str(value).replace("−", "-").translate(_SUPERSCRIPT_MAP)\n\n\ndef normalize_scientific_notation(value):\n    """Render common scientific-notation forms without relying on LaTeX support."""\n    text_value = str(value or "")\n    text_value = text_value.replace("\\\\times", "×").replace("\\\\cdot", "·")\n    text_value = text_value.replace("\\\\(", "").replace("\\\\)", "")\n    text_value = re.sub(\n        r"(?i)\\b([+-]?\\d+(?:\\.\\d+)?)\\s*[eE]([+\\-−]?\\d+)\\b",\n        lambda match: f"{match.group(1)} × 10{_to_superscript(match.group(2))}",\n        text_value,\n    )\n    text_value = re.sub(\n        r"10\\s*\\^\\s*\\{?\\s*([+\\-−]?\\d+)\\s*\\}?",\n        lambda match: "10" + _to_superscript(match.group(1)),\n        text_value,\n    )\n    # Remove simple math delimiters after converting the notation itself.\n    text_value = re.sub(r"\\$([^$]*(?:10[⁺⁻⁰¹²³⁴⁵⁶⁷⁸⁹]|×\\s*10)[^$]*)\\$", r"\\1", text_value)\n    return text_value\n\n\nDEFAULT_STATE = {\n''',
    'scientific notation helper',
)

# Tell the AI to emit browser-stable notation too.
replace_once(
    '7. 四個選項應使用一致的語法層級。\n\n【每題資料】',
    '7. 四個選項應使用一致的語法層級。\n8. 科學記號請使用一般文字與 Unicode 上標，例如 1 × 10⁶、3.2 × 10⁻⁴；不要輸出 LaTeX、$...$ 或 10^6。\n\n【每題資料】',
    'AI scientific notation instruction',
)

# 2) Center the uploader CTA inside the intro card.
replace_once(
    '''    [class*="st-key-material_intro_uploader"] { margin-top:1.15rem; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] { border:none !important; background:transparent !important; padding:0 !important; }\n''',
    '''    [class*="st-key-material_intro_uploader"] { margin-top:1.15rem; display:flex; justify-content:center; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] { border:none !important; background:transparent !important; padding:0 !important; width:100% !important; display:flex !important; justify-content:center !important; }\n''',
    'center uploader container',
)
replace_once(
    '''    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button { width:100% !important; min-height:48px !important; background:#31c978 !important; color:white !important; border:1px solid #31c978 !important; border-radius:15px !important; font-size:0 !important; }\n''',
    '''    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button { width:min(100%,360px) !important; min-height:48px !important; margin:0 auto !important; display:flex !important; align-items:center !important; justify-content:center !important; text-align:center !important; background:#31c978 !important; color:white !important; border:1px solid #31c978 !important; border-radius:15px !important; font-size:0 !important; }\n''',
    'center uploader button',
)

# 3) Small inline official-source link inside the question card.
replace_once(
    '    .quiz-question { color:#173b2b; font-size:1.22rem; line-height:1.65; font-weight:850; }\n',
    '''    .quiz-question { color:#173b2b; font-size:1.22rem; line-height:1.65; font-weight:850; }\n    .quiz-meta-row { display:flex; align-items:center; justify-content:space-between; gap:.75rem; flex-wrap:wrap; margin-bottom:.45rem; }\n    .official-inline-link { display:inline-flex; align-items:center; justify-content:center; padding:.34rem .62rem; border-radius:10px; background:#20252d; color:#fff !important; text-decoration:none !important; font-size:.78rem; font-weight:800; line-height:1.2; white-space:nowrap; }\n    .official-inline-link:hover { opacity:.88; }\n''',
    'inline official link CSS',
)

# 4) Avoid the extra rerun/old-study-page flash when entering a learning mode.
replace_once(
    '''def goto(page):\n    st.session_state.medslime_page = page\n    st.session_state.menu_open = False\n    st.rerun()\n\n\ndef render_drawer():\n''',
    '''def goto(page):\n    st.session_state.medslime_page = page\n    st.session_state.menu_open = False\n    st.rerun()\n\n\ndef set_page_without_extra_rerun(page):\n    """Widget callback: Streamlit will perform the normal rerun after this returns."""\n    st.session_state.medslime_page = page\n    st.session_state.menu_open = False\n\n\ndef render_drawer():\n''',
    'navigation callback helper',
)
replace_once(
    '''                if target:\n                    if st.button(f"進入 {title} →", key=f"go_{target}", use_container_width=True, type="primary"):\n                        goto(target)\n                else:\n                    st.button("即將開放", key=f"soon_{title}", use_container_width=True, disabled=True)\n''',
    '''                if target:\n                    st.button(\n                        f"進入 {title} →",\n                        key=f"go_{target}",\n                        use_container_width=True,\n                        type="primary",\n                        on_click=set_page_without_extra_rerun,\n                        args=(target,),\n                    )\n                else:\n                    st.button("即將開放", key=f"soon_{title}", use_container_width=True, disabled=True)\n''',
    'study navigation single rerun',
)

# 5) National-exam question header: remove duplicate top-left counter, put progress + source link in the card.
old_exam_header = '''    st.markdown(f'<div class="quiz-topline"><span class="quiz-count">第 {index + 1} / {len(questions)} 題</span></div>', unsafe_allow_html=True)\n    render_national_exam_progress(index, len(questions))\n    official = f'<div class="eyebrow">官方第 {official_number} 題</div>' if official_number is not None else ''\n    st.markdown(f'<div class="quiz-card">{official}<div class="quiz-question" style="margin-top:.25rem">{html.escape(str(question["question"]))}</div></div>', unsafe_allow_html=True)\n    if question.get("source_url"):\n        st.link_button("查看官方原題 ↗", question["source_url"])\n'''
new_exam_header = '''    render_national_exam_progress(index, len(questions))\n    remaining = sum(\n        1\n        for question_index in range(len(questions))\n        if _national_question_progress_state(question_index) in ("gray", "red")\n    )\n    progress_text = f"第 {index + 1} / {len(questions)} 題 · 尚有 {remaining} 題未作答"\n    source_link = ""\n    if question.get("source_url"):\n        safe_url = html.escape(str(question["source_url"]), quote=True)\n        source_link = f'<a class="official-inline-link" href="{safe_url}" target="_blank" rel="noopener noreferrer">官方原題 ↗</a>'\n    safe_exam_question = html.escape(normalize_scientific_notation(question["question"]))\n    st.markdown(\n        f'<div class="quiz-card"><div class="quiz-meta-row"><div class="eyebrow">{progress_text}</div>{source_link}</div><div class="quiz-question">{safe_exam_question}</div></div>',\n        unsafe_allow_html=True,\n    )\n'''
replace_once(old_exam_header, new_exam_header, 'national exam question header')

# 6) Apply notation formatting to radio options and material question text.
replace_once(
    '    safe_question = html.escape(str(question["question"]))\n',
    '    safe_question = html.escape(normalize_scientific_notation(question["question"]))\n',
    'material question notation',
)
replace_once(
    '    selected = st.radio("選擇答案", options, index=None, key=answer_key, label_visibility="collapsed")\n    uncertain = st.checkbox("❓ 我不確定這個觀念", key=uncertain_key)\n',
    '    selected = st.radio("選擇答案", options, index=None, key=answer_key, label_visibility="collapsed", format_func=normalize_scientific_notation)\n    uncertain = st.checkbox("❓ 我不確定這個觀念", key=uncertain_key)\n',
    'material radio notation',
)
replace_once(
    '    selected = st.radio("選擇答案", options, index=None, key=answer_key, label_visibility="collapsed")\n    uncertain = st.checkbox("❓ 我不確定這個觀念", key=uncertain_key)\n',
    '    selected = st.radio("選擇答案", options, index=None, key=answer_key, label_visibility="collapsed", format_func=normalize_scientific_notation)\n    uncertain = st.checkbox("❓ 我不確定這個觀念", key=uncertain_key)\n',
    'national radio notation',
)

# Review cards also get stable notation formatting.
replace_once(
    "f'<div class=\"{cls}\"><span class=\"review-option-letter\">{letters[idx] if idx < 4 else idx + 1}</span>{html.escape(str(option))}</div>'",
    "f'<div class=\"{cls}\"><span class=\"review-option-letter\">{letters[idx] if idx < 4 else idx + 1}</span>{html.escape(normalize_scientific_notation(option))}</div>'",
    'review option notation',
)
replace_once(
    'f\'<div class="result-card"><div class="eyebrow">官方第 {official} 題 · {tag}</div><div class="card-title" style="margin-top:.35rem">{html.escape(str(question["question"]))}</div>{review_options_markup(question, answer)}</div>\'',
    'f\'<div class="result-card"><div class="eyebrow">官方第 {official} 題 · {tag}</div><div class="card-title" style="margin-top:.35rem">{html.escape(normalize_scientific_notation(question["question"]))}</div>{review_options_markup(question, answer)}</div>\'',
    'national result question notation',
)
replace_once(
    'f\'<div class="result-card"><div class="eyebrow">Q{index + 1} · {tag}</div><div class="card-title" style="margin-top:.35rem">{html.escape(str(question["question"]))}</div>{review_options_markup(question, answer)}</div>\'',
    'f\'<div class="result-card"><div class="eyebrow">Q{index + 1} · {tag}</div><div class="card-title" style="margin-top:.35rem">{html.escape(normalize_scientific_notation(question["question"]))}</div>{review_options_markup(question, answer)}</div>\'',
    'material result question notation',
)
replace_once(
    '                st.markdown(f"**解析**  \\n{question[\'explanation\']}")\n',
    '                st.markdown(f"**解析**  \\n{normalize_scientific_notation(question[\'explanation\'])}")\n',
    'material explanation notation',
)

path.write_text(text, encoding='utf-8')
print('patched streamlit_app.py')
