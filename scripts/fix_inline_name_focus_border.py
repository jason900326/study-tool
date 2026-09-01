from pathlib import Path

p = Path('streamlit_app.py')
s = p.read_text(encoding='utf-8')
old = '''[class*="st-key-inline_name_"]:focus-within [data-baseweb="input"]{background:#f5faf7!important;border-color:#cfe7d8!important;box-shadow:0 0 0 1px #cfe7d8!important}[class*="st-key-inline_name_"] input:focus{background:#f5faf7!important}'''
new = '''[class*="st-key-inline_name_"]:focus-within [data-baseweb="input"]{background:#ffffff!important;border-color:#262730!important;box-shadow:none!important}[class*="st-key-inline_name_"] input:focus{background:#ffffff!important}'''
if old not in s:
    raise RuntimeError('inline focus css anchor not found')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('restored simple dark focus border for inline nickname')
