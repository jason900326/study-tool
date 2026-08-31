from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 match, got {count}')
    text = text.replace(old, new, 1)


# 1) Cache national-exam subject lookup so entering the page does not wait on Supabase.
if '@st.cache_data(ttl=1800, show_spinner=False)\ndef load_national_exam_subject_entries' not in text:
    replace_once(
        'def load_national_exam_subject_entries(exam_year):\n',
        '@st.cache_data(ttl=1800, show_spinner=False)\ndef load_national_exam_subject_entries(exam_year):\n',
        'cache exam subject entries',
    )

# 2) Warm the cache while the Study page is already visible.
needle = '''        st.write("")\n\n\ndef _queue_national_exam_choice'''
replacement = '''        st.write("")\n\n    # Warm the current-year exam subject list while the Study page is already open.\n    # This avoids leaving the old cards on screen while Supabase is queried after navigation.\n    try:\n        load_national_exam_subject_entries(int(st.session_state.national_exam_year))\n    except Exception:\n        pass\n\n\ndef _queue_national_exam_choice'''
if replacement not in text:
    replace_once(needle, replacement, 'prefetch exam subjects')

# 3) Remove the inline desktop-only font size and shorten the title so mobile wrapping is deterministic.
old_title = '''<div class="hero-title" style="font-size:2rem">上傳教材，AI 直接生成 10 題<br>開始你的專屬測驗。</div>'''
new_title = '''<div class="hero-title material-intro-title">上傳教材，AI 生成 10 題<br>開始你的專屬測驗。</div>'''
if new_title not in text:
    replace_once(old_title, new_title, 'material intro title')

# 4) Explicit responsive typography for this card only; do not depend on the global hero rule.
css_anchor = '''    [class*="st-key-material_intro_card"] { max-width:840px; margin:.3rem auto 1.15rem; background:rgba(255,255,255,.76); border:1px solid #dfebe4; border-radius:30px; padding:2rem 2rem 1.75rem; box-shadow:0 16px 38px rgba(30,82,51,.055); text-align:center; }\n'''
css_replacement = css_anchor + '''    [class*="st-key-material_intro_card"] .material-intro-title { font-size:2rem; line-height:1.18; }\n'''
if '[class*="st-key-material_intro_card"] .material-intro-title { font-size:2rem;' not in text:
    replace_once(css_anchor, css_replacement, 'material title desktop css')

mobile_anchor = '''    @media (max-width:700px) {\n        .block-container { padding-left:.85rem; padding-right:.85rem; padding-bottom:3rem; }\n'''
mobile_replacement = '''    @media (max-width:700px) {\n        .block-container { padding-left:.85rem; padding-right:.85rem; padding-bottom:3rem; }\n        [class*="st-key-material_intro_card"] { padding:1.45rem 1.05rem 1.3rem !important; border-radius:24px !important; }\n        [class*="st-key-material_intro_card"] .material-intro-title { font-size:1.42rem !important; line-height:1.28 !important; letter-spacing:-.025em !important; max-width:100% !important; overflow-wrap:normal !important; word-break:keep-all !important; }\n        [class*="st-key-material_intro_card"] .hero-copy { font-size:.92rem !important; line-height:1.65 !important; }\n        [class*="st-key-material_intro_card"] .intro-art { transform:scale(.88); transform-origin:center bottom; margin-bottom:-.1rem; }\n'''
if 'material-intro-title { font-size:1.42rem !important;' not in text:
    replace_once(mobile_anchor, mobile_replacement, 'material title mobile css')

path.write_text(text, encoding='utf-8')
print('patched streamlit_app.py')
