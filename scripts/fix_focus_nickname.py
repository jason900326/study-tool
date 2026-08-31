from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')
old = 'st.markdown(f\'<div class="focus-sub">{st.session_state.selected_slime} 正陪你往終點前進{paused_text}</div>\', unsafe_allow_html=True)'
new = 'companion_nickname = st.session_state.slime_nicknames.get(st.session_state.selected_slime, st.session_state.selected_slime)\n            st.markdown(f\'<div class="focus-sub">{html.escape(companion_nickname)} 正陪你往終點前進{paused_text}</div>\', unsafe_allow_html=True)'
if old not in text:
    raise RuntimeError('focus subtitle anchor not found')
text = text.replace(old, new, 1)
path.write_text(text, encoding='utf-8')
print('focus subtitle now uses nickname')
