from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

# Add compact styling for the source button inside the question card container.
css_anchor = '''    .official-inline-link:hover { opacity:.88; }\n'''
css_insert = css_anchor + '''    [class*="st-key-exam_question_card_"] { background:rgba(255,255,255,.96); border:1px solid #dceae2; border-radius:27px; padding:1.55rem 1.6rem .9rem; box-shadow:0 14px 34px rgba(31,83,53,.06); animation:questionIn .22s ease-out both; margin-bottom:.8rem; }\n    [class*="st-key-exam_question_card_"] .quiz-card { background:transparent !important; border:0 !important; box-shadow:none !important; padding:0 !important; margin:0 !important; animation:none !important; }\n    [class*="st-key-exam_source_compact_"] { display:flex; justify-content:flex-end; margin-top:.45rem; }\n    [class*="st-key-exam_source_compact_"] button { min-height:32px !important; height:32px !important; width:auto !important; padding:.22rem .68rem !important; border-radius:10px !important; font-size:.76rem !important; font-weight:800 !important; box-shadow:none !important; }\n    [class*="st-key-exam_source_compact_"] button p { font-size:.76rem !important; white-space:nowrap !important; }\n'''
if '[class*="st-key-exam_question_card_"]' not in text:
    if css_anchor not in text:
        raise RuntimeError('source CSS anchor not found')
    text = text.replace(css_anchor, css_insert, 1)

old = '''    safe_exam_question = html.escape(normalize_scientific_notation(question["question"]))\n    st.markdown(\n        f'<div class="quiz-card"><div class="quiz-meta-row"><div class="eyebrow">{progress_text}</div></div><div class="quiz-question">{safe_exam_question}</div></div>',\n        unsafe_allow_html=True,\n    )\n    if question.get("has_image_hint"):\n'''
new = '''    safe_exam_question = html.escape(normalize_scientific_notation(question["question"]))\n    with st.container(key=f"exam_question_card_{index}"):\n        st.markdown(\n            f'<div class="quiz-card"><div class="quiz-meta-row"><div class="eyebrow">{progress_text}</div></div><div class="quiz-question">{safe_exam_question}</div></div>',\n            unsafe_allow_html=True,\n        )\n        if question.get("source_url") or question.get("question_pdf_url"):\n            with st.container(key=f"exam_source_compact_{index}"):\n                st.button(\n                    "📄 官方原題",\n                    key=f"exam_source_{index}",\n                    on_click=open_pdf_viewer,\n                    args=(question, "national_exam_quiz"),\n                )\n    if question.get("has_image_hint"):\n'''
if old not in text:
    raise RuntimeError('question card anchor not found')
text = text.replace(old, new, 1)

old_source = '''    if question.get("source_url") or question.get("question_pdf_url"):\n        page_hint = question.get("source_page")\n        source_label = f"📄 查看官方原題 · PDF 第 {page_hint} 頁" if page_hint else "📄 查看官方原題"\n        st.button(\n            source_label,\n            key=f"exam_source_{index}",\n            use_container_width=True,\n            on_click=open_pdf_viewer,\n            args=(question, "national_exam_quiz"),\n        )\n\n    answer_key = f"exam_answer_{index}"\n'''
new_source = '''    answer_key = f"exam_answer_{index}"\n'''
if old_source not in text:
    raise RuntimeError('old full-width source button block not found')
text = text.replace(old_source, new_source, 1)

path.write_text(text, encoding='utf-8')
print('compacted official-source button into question card')
