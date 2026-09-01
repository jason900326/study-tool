from pathlib import Path

p = Path('streamlit_app.py')
s = p.read_text(encoding='utf-8')
old = '''[class*="st-key-inline_name_"]{position:relative;margin:.15rem auto .05rem!important;max-width:100%}[class*="st-key-inline_name_"] input{background:transparent!important;border:0!important;box-shadow:none!important;text-align:center!important;font-weight:900!important;color:#1c4130!important;font-size:.9rem!important;padding:.15rem 1.7rem .15rem .35rem!important;min-height:2rem!important}[class*="st-key-inline_name_"] input:focus{background:#f5faf7!important;box-shadow:0 0 0 1px #cfe7d8!important;border-radius:9px!important}[class*="st-key-inline_name_"]::after{content:"✏️";position:absolute;right:.45rem;top:50%;transform:translateY(-50%);font-size:.78rem;pointer-events:none}'''
new = '''[class*="st-key-inline_name_"]{position:relative;margin:.15rem auto .05rem!important;max-width:100%}[class*="st-key-inline_name_"] [data-baseweb="input"]{background:#ffffff!important;border:1px solid transparent!important;border-radius:9px!important;box-shadow:none!important}[class*="st-key-inline_name_"] input{background:#ffffff!important;border:0!important;box-shadow:none!important;text-align:center!important;font-weight:900!important;color:#1c4130!important;-webkit-text-fill-color:#1c4130!important;caret-color:#1c4130!important;font-size:.9rem!important;padding:.15rem 1.7rem .15rem .35rem!important;min-height:2rem!important}[class*="st-key-inline_name_"]:focus-within [data-baseweb="input"]{background:#f5faf7!important;border-color:#cfe7d8!important;box-shadow:0 0 0 1px #cfe7d8!important}[class*="st-key-inline_name_"] input:focus{background:#f5faf7!important}[class*="st-key-inline_name_"]::after{content:"✏️";position:absolute;right:.45rem;top:50%;transform:translateY(-50%);font-size:.78rem;pointer-events:none}'''
if old not in s:
    raise RuntimeError('inline name css anchor not found')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('fixed inline nickname input background')
