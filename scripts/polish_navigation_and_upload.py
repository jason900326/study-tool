from pathlib import Path
import re

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 match, got {count}')
    text = text.replace(old, new, 1)


# 1) Center the visible file-uploader CTA exactly. Hide the native upload icon and
# place our label absolutely across the full button so the visual center is real.
old_button_css = '''    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button { width:min(100%,360px) !important; min-height:48px !important; margin:0 auto !important; display:flex !important; align-items:center !important; justify-content:center !important; text-align:center !important; background:#31c978 !important; color:white !important; border:1px solid #31c978 !important; border-radius:15px !important; font-size:0 !important; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button p,\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button span { font-size:0 !important; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button::after { content:"☁️ 上傳教材開始學習"; font-size:.95rem; font-weight:850; }\n'''
new_button_css = '''    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button { width:min(100%,360px) !important; min-height:48px !important; margin:0 auto !important; position:relative !important; display:flex !important; align-items:center !important; justify-content:center !important; text-align:center !important; background:#31c978 !important; color:white !important; border:1px solid #31c978 !important; border-radius:15px !important; font-size:0 !important; overflow:hidden !important; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button p,\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button span,\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button svg { display:none !important; font-size:0 !important; }\n    [class*="st-key-material_intro_uploader"] [data-testid="stFileUploaderDropzone"] button::after { content:"☁️  上傳教材開始學習"; position:absolute !important; inset:0 !important; display:flex !important; align-items:center !important; justify-content:center !important; text-align:center !important; font-size:.95rem; font-weight:850; line-height:1 !important; }\n'''
replace_once(old_button_css, new_button_css, 'center uploader CTA')

# 2) Study cards: keep the card title as the context and make the action concise.
replace_once(
    '                        f"進入 {title} →",\n',
    '                        "進入 →",\n',
    'study card enter label',
)

# 3) Shared return button helper.
helper_anchor = '''def set_page_without_extra_rerun(page):\n    st.session_state.medslime_page = page\n    st.session_state.menu_open = False\n\n\ndef render_drawer():\n'''
helper_replacement = '''def set_page_without_extra_rerun(page):\n    st.session_state.medslime_page = page\n    st.session_state.menu_open = False\n\n\ndef render_back_button(label, target, key):\n    st.button(\n        f"← {label}",\n        key=key,\n        on_click=set_page_without_extra_rerun,\n        args=(target,),\n    )\n\n\ndef render_drawer():\n'''
if 'def render_back_button(' not in text:
    replace_once(helper_anchor, helper_replacement, 'shared back button helper')

# 4) Add consistent back navigation to major subpages.
# Existing study_material_intro already has the liked "返回學習" button, so leave it unchanged.
page_specs = [
    ('study_home', '返回首頁', 'home', 'back_study_home'),
    ('national_exam_home', '返回學習', 'study', 'back_national_exam_home'),
    ('national_exam_quiz_page', '返回國考', 'national_exam', 'back_national_exam_quiz'),
    ('national_exam_result_page', '返回國考', 'national_exam', 'back_national_exam_result'),
    ('material_quiz_page', '返回教材', 'study_material_intro', 'back_material_quiz'),
    ('quiz_result_page', '返回教材', 'study_material_intro', 'back_material_result'),
    ('slime_page', '返回首頁', 'home', 'back_slime'),
    ('gacha_page', '返回首頁', 'home', 'back_gacha'),
    ('achievements_page', '返回首頁', 'home', 'back_achievements'),
]

patched = []
for func_name, label, target, key in page_specs:
    if f'key="{key}"' in text:
        continue
    pattern = rf'(def {re.escape(func_name)}\(\):\n    topbar\(\)\n)'
    replacement = rf'\1    render_back_button("{label}", "{target}", "{key}")\n'
    text, count = re.subn(pattern, replacement, text, count=1)
    if count:
        patched.append(func_name)

print('back buttons patched:', patched)
path.write_text(text, encoding='utf-8')
print('patched streamlit_app.py')
