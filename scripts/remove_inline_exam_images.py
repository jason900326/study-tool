from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

# Remove the inline image rendering block from the national exam quiz page.
start_marker = '''    if question.get("has_image_hint"):\n        inline_url = question.get("question_pdf_url") or question.get("source_url")\n'''
end_marker = '''    answer_key = f"exam_answer_{index}"\n'''
start = text.find(start_marker)
if start == -1:
    raise RuntimeError('inline image block start not found')
end = text.find(end_marker, start)
if end == -1:
    raise RuntimeError('inline image block end not found')
text = text[:start] + end_marker + text[end + len(end_marker):]

# Remove figure label CSS now that inline images are not rendered.
text = text.replace('    .exam-inline-figure-label { color:#6b8275; font-size:.78rem; font-weight:800; text-align:center; margin:.15rem 0 .35rem; }\n', '')

path.write_text(text, encoding='utf-8')
print('removed inline exam image rendering; official source link remains')
