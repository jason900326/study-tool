from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

# 1) Do not exclude image-hint questions from national exam papers.
old_filter = '''        if row.get("parse_status") != "ok":\n            reason = "解析異常"\n        elif row.get("has_image_hint"):\n            reason = "需要圖片"\n        elif len(options) != 4:\n            reason = "選項不完整"\n'''
new_filter = '''        if row.get("parse_status") != "ok":\n            reason = "解析異常"\n        elif len(options) != 4:\n            reason = "選項不完整"\n'''
if old_filter not in text:
    raise RuntimeError('image exclusion filter anchor not found')
text = text.replace(old_filter, new_filter, 1)

# 2) Preserve image-hint metadata on loaded question objects.
old_question_dict = '''            "source_page": _extract_pdf_page_hint(row.get("source_page_url")) or _extract_pdf_page_hint(row.get("question_pdf_url")),\n            "official_question_number": number,\n            "national_exam_id": row.get("id"),\n'''
new_question_dict = '''            "source_page": _extract_pdf_page_hint(row.get("source_page_url")) or _extract_pdf_page_hint(row.get("question_pdf_url")),\n            "has_image_hint": bool(row.get("has_image_hint")),\n            "official_question_number": number,\n            "national_exam_id": row.get("id"),\n'''
if old_question_dict not in text:
    raise RuntimeError('question dict anchor not found')
text = text.replace(old_question_dict, new_question_dict, 1)

# 3) Remove the explanatory subtitle from the internal official-source viewer.
old_viewer_header = '''    st.markdown(\n        f'<div class="study-header"><div class="eyebrow">SOURCE</div>'\n        f'<div class="hero-title" style="font-size:2rem">{html.escape(str(title))}</div>'\n        f'<div class="hero-copy">直接顯示原 PDF 的定位頁，不依賴手機瀏覽器的 PDF 跳頁功能。</div></div>',\n        unsafe_allow_html=True,\n    )\n'''
new_viewer_header = '''    st.markdown(\n        f'<div class="study-header"><div class="eyebrow">SOURCE</div>'\n        f'<div class="hero-title" style="font-size:2rem">{html.escape(str(title))}</div></div>',\n        unsafe_allow_html=True,\n    )\n'''
if old_viewer_header not in text:
    raise RuntimeError('viewer subtitle anchor not found')
text = text.replace(old_viewer_header, new_viewer_header, 1)

# 4) Show a concise hint on image-dependent questions.
old_quiz_source = '''    if question.get("source_url") or question.get("question_pdf_url"):\n        page_hint = question.get("source_page")\n        source_label = f"📄 查看官方原題 · PDF 第 {page_hint} 頁" if page_hint else "📄 查看官方原題"\n        st.button(\n            source_label,\n            key=f"exam_source_{index}",\n            use_container_width=True,\n            on_click=open_pdf_viewer,\n            args=(question, "national_exam_quiz"),\n        )\n\n    answer_key = f"exam_answer_{index}"\n'''
new_quiz_source = '''    if question.get("has_image_hint"):\n        st.info("本題含圖片，請查看官方原題後再作答。")\n    if question.get("source_url") or question.get("question_pdf_url"):\n        page_hint = question.get("source_page")\n        source_label = f"📄 查看官方原題 · PDF 第 {page_hint} 頁" if page_hint else "📄 查看官方原題"\n        st.button(\n            source_label,\n            key=f"exam_source_{index}",\n            use_container_width=True,\n            on_click=open_pdf_viewer,\n            args=(question, "national_exam_quiz"),\n        )\n\n    answer_key = f"exam_answer_{index}"\n'''
if old_quiz_source not in text:
    raise RuntimeError('quiz source anchor not found')
text = text.replace(old_quiz_source, new_quiz_source, 1)

path.write_text(text, encoding='utf-8')
print('restored image national-exam questions and removed viewer subtitle')
