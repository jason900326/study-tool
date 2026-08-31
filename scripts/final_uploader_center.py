from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

old = '''    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button { width:min(100%,360px) !important; min-height:48px !important; margin:0 auto !important; display:flex !important; align-items:center !important; justify-content:center !important; text-align:center !important; background:#31c978 !important; color:white !important; border:1px solid #31c978 !important; border-radius:15px !important; font-size:0 !important; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button p,\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button span { font-size:0 !important; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button::after { content:"☁️ 上傳教材開始學習"; font-size:.95rem; font-weight:850; }\n'''
new = '''    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button { width:min(100%,360px) !important; min-height:48px !important; margin:0 auto !important; position:relative !important; display:block !important; text-align:center !important; background:#31c978 !important; color:white !important; border:1px solid #31c978 !important; border-radius:15px !important; font-size:0 !important; overflow:hidden !important; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button p,\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button span,\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button svg { font-size:0 !important; opacity:0 !important; visibility:hidden !important; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button::after { content:"☁️ 上傳教材開始學習"; position:absolute !important; left:50% !important; top:50% !important; transform:translate(-50%,-50%) !important; width:100% !important; margin:0 !important; padding:0 .75rem !important; box-sizing:border-box !important; text-align:center !important; white-space:nowrap !important; font-size:.95rem; font-weight:850; line-height:1.2; }\n'''
if old not in text:
    raise RuntimeError('uploader CSS target not found')
text = text.replace(old, new, 1)

old_intro = '''def study_material_intro():\n    topbar()\n    if st.button("← 返回學習", key="intro_back"):\n        goto("study")\n'''
new_intro = '''def study_material_intro():\n    topbar()\n    render_back_button("返回學習", "study", "intro_back")\n'''
if old_intro in text:
    text = text.replace(old_intro, new_intro, 1)

path.write_text(text, encoding='utf-8')
print('centered uploader and unified intro back button')
