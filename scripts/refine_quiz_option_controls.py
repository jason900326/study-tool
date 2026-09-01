from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

# Shorten uncertainty label in both national-exam and material quizzes.
text = text.replace('st.checkbox("❓ 我不確定這個觀念", key=uncertain_key)', 'st.checkbox("❓ 我不確定", key=uncertain_key)')

# Strengthen the option-text styling: plain text-like clickable row, left aligned, no card border/background.
old_css = '''    [class*="st-key-national_strike_"] button,\n    [class*="st-key-material_strike_"] button { justify-content:flex-start !important; text-align:left !important; background:rgba(255,255,255,.82) !important; color:#244c39 !important; border:1px solid #e0ebe5 !important; box-shadow:none !important; padding-left:.9rem !important; }\n    [class*="st-key-national_strike_"] button p,\n    [class*="st-key-material_strike_"] button p { width:100% !important; text-align:left !important; }\n'''
new_css = '''    [class*="st-key-national_strike_"] button,\n    [class*="st-key-material_strike_"] button {\n        justify-content:flex-start !important;\n        text-align:left !important;\n        background:transparent !important;\n        color:#244c39 !important;\n        border:none !important;\n        box-shadow:none !important;\n        border-radius:0 !important;\n        padding:.45rem .15rem !important;\n        min-height:38px !important;\n        width:100% !important;\n    }\n    [class*="st-key-national_strike_"] button:hover,\n    [class*="st-key-material_strike_"] button:hover { background:transparent !important; border:none !important; box-shadow:none !important; transform:none !important; }\n    [class*="st-key-national_strike_"] button > div,\n    [class*="st-key-material_strike_"] button > div,\n    [class*="st-key-national_strike_"] [data-testid="stMarkdownContainer"],\n    [class*="st-key-material_strike_"] [data-testid="stMarkdownContainer"],\n    [class*="st-key-national_strike_"] button p,\n    [class*="st-key-material_strike_"] button p {\n        width:100% !important;\n        justify-content:flex-start !important;\n        text-align:left !important;\n        margin:0 !important;\n    }\n'''
if old_css not in text:
    raise RuntimeError('option text CSS anchor not found')
text = text.replace(old_css, new_css, 1)

# Make the uncertainty checkbox visually circular so it matches answer selectors.
anchor = '''    [data-testid="stCheckbox"] { margin-top:.35rem; margin-bottom:.7rem; }\n'''
addition = '''    [data-testid="stCheckbox"] { margin-top:.35rem; margin-bottom:.7rem; }\n    [data-testid="stCheckbox"] input + div,\n    [data-testid="stCheckbox"] [data-testid="stCheckbox"] { border-radius:50% !important; }\n    [data-testid="stCheckbox"] svg { border-radius:50% !important; }\n    [data-testid="stCheckbox"] label > div:first-child { border-radius:50% !important; }\n'''
if anchor not in text:
    raise RuntimeError('checkbox CSS anchor not found')
text = text.replace(anchor, addition, 1)

path.write_text(text, encoding='utf-8')
print('refined quiz option controls')
