from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

old = 'button::after { content:"☁️  上傳教材開始學習";'
new = 'button::after { content:"上傳教材開始學習";'
if old not in text:
    raise RuntimeError('uploader label target not found')
text = text.replace(old, new, 1)

old_intro = '''def study_material_intro():\n    topbar()\n    if st.button("← 返回學習", key="intro_back"):\n        goto("study")\n'''
new_intro = '''def study_material_intro():\n    topbar()\n    render_back_button("返回學習", "study", "intro_back")\n'''
if old_intro in text:
    text = text.replace(old_intro, new_intro, 1)

path.write_text(text, encoding='utf-8')
print('fixed optical centering and unified intro back button')
