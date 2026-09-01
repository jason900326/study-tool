from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

css_anchor = '''    .digest-card { max-width:620px;'''
if css_anchor not in text:
    raise RuntimeError('digest css anchor not found')

css_insert = '''    .material-processing-overlay {
        position:fixed;
        inset:0;
        z-index:99990;
        display:flex;
        align-items:flex-start;
        justify-content:center;
        padding:5.4rem 1rem 2rem;
        overflow:auto;
        background:
            radial-gradient(circle at 8% 3%, rgba(130,239,173,.18), transparent 24%),
            radial-gradient(circle at 93% 13%, rgba(118,220,255,.15), transparent 23%),
            #f8fcf9;
        animation:processingOverlayIn .16s ease-out both;
    }
    .material-processing-overlay .digest-card {
        width:min(620px, calc(100vw - 2rem));
        margin:0 auto;
    }
'''
if '.material-processing-overlay {' not in text:
    text = text.replace(css_anchor, css_insert + css_anchor, 1)

anim_anchor = '''    @keyframes pageIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }\n'''
anim_new = anim_anchor + '''    @keyframes processingOverlayIn { from { opacity:0; } to { opacity:1; } }\n'''
if '@keyframes processingOverlayIn' not in text:
    if anim_anchor not in text:
        raise RuntimeError('animation anchor not found')
    text = text.replace(anim_anchor, anim_new, 1)

mobile_anchor = '''        .block-container { padding-left:.85rem; padding-right:.85rem; padding-bottom:3rem; }\n'''
mobile_new = mobile_anchor + '''        .material-processing-overlay { padding:4.4rem .75rem 1.5rem; align-items:flex-start; }\n        .material-processing-overlay .digest-card { width:calc(100vw - 1.5rem); }\n'''
if '        .material-processing-overlay { padding:4.4rem' not in text:
    if mobile_anchor not in text:
        raise RuntimeError('mobile anchor not found')
    text = text.replace(mobile_anchor, mobile_new, 1)

old_func = '''def render_loading_card(filename):\n    st.markdown(\n        f'<div class="digest-card"><div class="digest-slime"></div><div class="card-title" style="font-size:1.25rem">史萊姆正在消化教材</div><div class="muted" style="margin-top:.45rem">{html.escape(str(filename))}</div><div class="hero-copy" style="margin-top:.75rem">正在讀取內容、整理概念並準備 {QUIZ_SIZE} 題測驗。</div><div class="digest-dots"><span>●</span><span>●</span><span>●</span></div></div>',\n        unsafe_allow_html=True,\n    )\n'''
new_func = '''def render_loading_card(filename, overlay=False):\n    card = f'<div class="digest-card"><div class="digest-slime"></div><div class="card-title" style="font-size:1.25rem">史萊姆正在消化教材</div><div class="muted" style="margin-top:.45rem">{html.escape(str(filename))}</div><div class="hero-copy" style="margin-top:.75rem">正在讀取內容、整理概念並準備 {QUIZ_SIZE} 題測驗。</div><div class="digest-dots"><span>●</span><span>●</span><span>●</span></div></div>'\n    if overlay:\n        card = f'<div class="material-processing-overlay">{card}</div>'\n    st.markdown(card, unsafe_allow_html=True)\n'''
if old_func not in text:
    raise RuntimeError('render_loading_card anchor not found')
text = text.replace(old_func, new_func, 1)

old_call = '''    render_loading_card(filename)\n\n    if not file_bytes or not file_hash:\n'''
new_call = '''    render_loading_card(filename, overlay=True)\n\n    if not file_bytes or not file_hash:\n'''
if old_call not in text:
    raise RuntimeError('processing render call anchor not found')
text = text.replace(old_call, new_call, 1)

path.write_text(text, encoding='utf-8')
print('added full material processing overlay')
