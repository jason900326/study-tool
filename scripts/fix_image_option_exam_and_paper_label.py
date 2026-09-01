from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

# 1) Keep image-dependent questions even when their option text / parse status is incomplete.
old_loader = '''    for row in rows:\n        options = row.get("options") or []\n        correct_answers = row.get("correct_answers") or []\n        reason = None\n        if row.get("parse_status") != "ok":\n            reason = "解析異常"\n        elif len(options) != 4:\n            reason = "選項不完整"\n        elif len(correct_answers) != 1 or correct_answers[0] not in answer_map:\n            reason = "多答案或答案格式特殊"\n\n        if reason:\n            excluded.append({"question_number": row.get("question_number"), "reason": reason})\n            continue\n\n        number = row.get("question_number")\n        usable.append({\n            "question": row.get("question") or "",\n            "options": options,\n'''
new_loader = '''    for row in rows:\n        options = list(row.get("options") or [])\n        correct_answers = row.get("correct_answers") or []\n        has_image_hint = bool(row.get("has_image_hint"))\n        valid_answer = len(correct_answers) == 1 and correct_answers[0] in answer_map\n        image_choice_mode = False\n        reason = None\n\n        # A valid official A-D answer is mandatory for every interactive question.\n        if not valid_answer:\n            reason = "多答案或答案格式特殊"\n        elif has_image_hint:\n            # Image questions are allowed even when the parser cannot reconstruct\n            # all four option texts. In that case, show the original PDF question\n            # inline and let the learner answer with A / B / C / D.\n            if row.get("parse_status") != "ok" or len(options) != 4:\n                options = ["A", "B", "C", "D"]\n                image_choice_mode = True\n        elif row.get("parse_status") != "ok":\n            reason = "解析異常"\n        elif len(options) != 4:\n            reason = "選項不完整"\n\n        if reason:\n            excluded.append({"question_number": row.get("question_number"), "reason": reason})\n            continue\n\n        number = row.get("question_number")\n        usable.append({\n            "question": row.get("question") or "",\n            "options": options,\n'''
if old_loader not in text:
    raise RuntimeError('loader block not found')
text = text.replace(old_loader, new_loader, 1)

old_meta = '''            "has_image_hint": bool(row.get("has_image_hint")),\n            "official_question_number": number,\n'''
new_meta = '''            "has_image_hint": has_image_hint,\n            "image_choice_mode": image_choice_mode,\n            "official_question_number": number,\n'''
if old_meta not in text:
    raise RuntimeError('question metadata block not found')
text = text.replace(old_meta, new_meta, 1)

# 2) Add right-aligned paper name styling inside the question card.
css_anchor = '''    [class*="st-key-exam_source_compact_"] button p { font-size:.76rem !important; white-space:nowrap !important; }\n'''
css_add = css_anchor + '''    .exam-paper-name { margin-left:auto; color:#789083; font-size:.78rem; font-weight:800; text-align:right; line-height:1.35; max-width:62%; }\n    @media (max-width:700px) { .exam-paper-name { max-width:58%; font-size:.7rem; } }\n'''
if '.exam-paper-name {' not in text:
    if css_anchor not in text:
        raise RuntimeError('compact source css anchor not found')
    text = text.replace(css_anchor, css_add, 1)

# 3) Put the active paper name at the right side of the card meta row.
old_card = '''    safe_exam_question = html.escape(normalize_scientific_notation(question["question"]))\n    with st.container(key=f"exam_question_card_{index}"):\n        st.markdown(\n            f'<div class="quiz-card"><div class="quiz-meta-row"><div class="eyebrow">{progress_text}</div></div><div class="quiz-question">{safe_exam_question}</div></div>',\n            unsafe_allow_html=True,\n        )\n'''
new_card = '''    safe_exam_question = html.escape(normalize_scientific_notation(question["question"]))\n    meta = st.session_state.national_exam_meta or {}\n    paper_name = f'{roc_year_label(meta.get("exam_year", 2026))} {meta.get("exam_round", "")} · {meta.get("subject", "")}'\n    safe_paper_name = html.escape(str(paper_name).strip())\n    with st.container(key=f"exam_question_card_{index}"):\n        st.markdown(\n            f'<div class="quiz-card"><div class="quiz-meta-row"><div class="eyebrow">{progress_text}</div><div class="exam-paper-name">{safe_paper_name}</div></div><div class="quiz-question">{safe_exam_question}</div></div>',\n            unsafe_allow_html=True,\n        )\n'''
if old_card not in text:
    raise RuntimeError('question card block not found')
text = text.replace(old_card, new_card, 1)

# 4) If the options themselves could not be parsed, show the full original question crop
# inline, not only extracted figures, so image-based answer choices remain visible.
old_inline_start = '''    if question.get("has_image_hint"):\n        inline_url = question.get("question_pdf_url") or question.get("source_url")\n        inline_number = question.get("official_question_number")\n        inline_images = []\n        if inline_url and inline_number:\n            try:\n                with st.spinner("正在載入題目圖片…"):\n                    inline_images = _render_pdf_question_images(inline_url, inline_number)\n            except Exception:\n                inline_images = []\n'''
new_inline_start = '''    if question.get("has_image_hint"):\n        inline_url = question.get("question_pdf_url") or question.get("source_url")\n        inline_number = question.get("official_question_number")\n        inline_images = []\n        if inline_url and inline_number:\n            try:\n                with st.spinner("正在載入題目圖片…"):\n                    if question.get("image_choice_mode"):\n                        crops, _ = _render_pdf_question_crops(inline_url, inline_number)\n                        inline_images = crops\n                    else:\n                        inline_images = _render_pdf_question_images(inline_url, inline_number)\n            except Exception:\n                inline_images = []\n'''
if old_inline_start not in text:
    raise RuntimeError('inline image block not found')
text = text.replace(old_inline_start, new_inline_start, 1)

path.write_text(text, encoding='utf-8')
print('patched image-option questions and paper label')
