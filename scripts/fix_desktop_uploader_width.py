from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

old = '''[class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button { width:min(100%,360px) !important; min-height:48px !important; margin:0 auto !important; position:relative !important; display:flex !important; align-items:center !important; justify-content:center !important; text-align:center !important; background:#31c978 !important; color:white !important; border:1px solid #31c978 !important; border-radius:15px !important; font-size:0 !important; overflow:hidden !important; }'''
new = '''[class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button { width:360px !important; max-width:100% !important; min-width:280px !important; min-height:48px !important; margin:0 auto !important; position:relative !important; display:flex !important; align-items:center !important; justify-content:center !important; text-align:center !important; background:#31c978 !important; color:white !important; border:1px solid #31c978 !important; border-radius:15px !important; font-size:0 !important; overflow:hidden !important; }'''

if old not in text:
    raise RuntimeError('desktop uploader button CSS target not found')
text = text.replace(old, new, 1)

mobile_anchor = '''    @media (max-width:700px) {\n        .block-container { padding-left:.85rem; padding-right:.85rem; padding-bottom:3rem; }'''
mobile_new = '''    @media (max-width:700px) {\n        .block-container { padding-left:.85rem; padding-right:.85rem; padding-bottom:3rem; }\n        [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button { width:100% !important; max-width:100% !important; min-width:0 !important; }'''
if mobile_new not in text:
    if mobile_anchor not in text:
        raise RuntimeError('mobile media anchor not found')
    text = text.replace(mobile_anchor, mobile_new, 1)

path.write_text(text, encoding='utf-8')
print('fixed desktop uploader width')
