from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

# Add name-editing state.
state_anchor = '    "slime_nicknames": {"青蘋果史萊姆": "Medi"},\n'
state_new = state_anchor + '    "slime_name_editing": False,\n'
if '    "slime_name_editing": False,\n' not in text:
    if state_anchor not in text:
        raise RuntimeError('nickname state anchor not found')
    text = text.replace(state_anchor, state_new, 1)

# Rarity badge text must stay white regardless of generic rarity classes below.
old_rarity_css = '''    .rarity-chip { background:#173b2b; color:#fff; }\n    .rarity-chip.rarity-R { background:#4d77bd; }\n    .rarity-chip.rarity-SR { background:#8b63bc; }\n    .rarity-chip.rarity-SSR { background:linear-gradient(90deg,#9d6bc3,#d88c61); }\n    .family-chip { background:#fff; border:1px solid #dceae2; color:#627d6f; }\n'''
new_rarity_css = '''    .rarity-chip { background:#173b2b; color:#fff !important; }\n    .rarity-chip.rarity-N { background:#173b2b; color:#fff !important; }\n    .rarity-chip.rarity-R { background:#4d77bd; color:#fff !important; }\n    .rarity-chip.rarity-SR { background:#8b63bc; color:#fff !important; }\n    .rarity-chip.rarity-SSR { background:linear-gradient(90deg,#9d6bc3,#d88c61); color:#fff !important; }\n    .family-chip { background:#fff; border:1px solid #dceae2; color:#627d6f; }\n'''
if old_rarity_css not in text:
    raise RuntimeError('rarity CSS anchor not found')
text = text.replace(old_rarity_css, new_rarity_css, 1)

# Name button and achievement card styling.
css_anchor = '    .companion-name { color:#173b2b; font-size:1.65rem; font-weight:950; letter-spacing:-.03em; margin:.2rem 0 .25rem; }\n'
css_add = css_anchor + '''    [class*="st-key-slime_name_button_"] button { background:transparent !important; border:none !important; box-shadow:none !important; min-height:0 !important; height:auto !important; padding:.08rem 0 .18rem !important; justify-content:flex-start !important; color:#173b2b !important; font-size:1.65rem !important; font-weight:950 !important; letter-spacing:-.03em !important; }\n    [class*="st-key-slime_name_button_"] button:hover,[class*="st-key-slime_name_button_"] button:focus,[class*="st-key-slime_name_button_"] button:active { background:transparent !important; border:none !important; box-shadow:none !important; transform:none !important; color:#1f8d56 !important; }\n    [class*="st-key-slime_name_button_"] button p { font-size:1.65rem !important; font-weight:950 !important; margin:0 !important; }\n    [class*="st-key-slime_nickname_editor_"] { max-width:420px; margin:.1rem 0 .5rem; }\n    .achievement-card { background:white; border:1px solid #dfebe4; border-radius:22px; padding:1rem; min-height:165px; margin-bottom:1rem; box-shadow:0 8px 22px rgba(31,83,53,.035); }\n    .achievement-card.locked { background:#f6f9f7; border-color:#e3ebe6; }\n    .achievement-icon { font-size:2rem; margin-bottom:.25rem; }\n    .achievement-card.locked .achievement-icon { filter:grayscale(1); opacity:.52; }\n    .achievement-title { color:#1d4533; font-weight:900; font-size:1.08rem; }\n    .achievement-card.locked .achievement-title { color:#53695d; }\n    .achievement-desc { color:#71887b; margin-top:.2rem; line-height:1.45; }\n    .achievement-card.locked .achievement-desc { color:#7c8f84; }\n    .achievement-status { margin-top:.65rem; font-weight:850; color:#258c55; }\n    .achievement-card.locked .achievement-status { color:#71857a; }\n'''
if '[class*="st-key-slime_name_button_"] button' not in text:
    if css_anchor not in text:
        raise RuntimeError('companion name CSS anchor not found')
    text = text.replace(css_anchor, css_add, 1)

# Remove family/series chip and static nickname from the companion markup.
old_panel = '''        f'<div class="companion-topline"><span class="rarity-chip {rarity_class}">{current["rarity"]}</span>'\n        f'<span class="family-chip">{current["family"]}</span><span class="owned-chip">✓ 陪伴中</span></div>'\n        f'<div class="companion-name">{html.escape(nickname)}</div>'\n        f'<div class="companion-species">{current["name"]} · {current["tagline"]}</div>'\n'''
new_panel = '''        f'<div class="companion-topline"><span class="rarity-chip {rarity_class}">{current["rarity"]}</span>'\n        f'<span class="owned-chip">✓ 陪伴中</span></div>'\n        f'<div class="companion-species">{current["name"]} · {current["tagline"]}</div>'\n'''
if old_panel not in text:
    raise RuntimeError('companion panel anchor not found')
text = text.replace(old_panel, new_panel, 1)

# Replace the always-visible nickname input with an inline name button + conditional editor.
old_input = '''    new_nickname = st.text_input("史萊姆暱稱", value=nickname, max_chars=16, key=f"nickname_{current['name']}")\n    if new_nickname != nickname:\n        st.session_state.slime_nicknames[current["name"]] = new_nickname.strip() or current["name"].replace("史萊姆", "")\n\n'''
new_input = '''    # The nickname itself is the edit control; keep the editor hidden until requested.\n    if st.button(f"{nickname} ✏️", key=f"slime_name_button_{current['theme']}"):\n        st.session_state.slime_name_editing = not st.session_state.slime_name_editing\n        st.rerun()\n    if st.session_state.slime_name_editing:\n        with st.container(key=f"slime_nickname_editor_{current['theme']}"):\n            new_nickname = st.text_input("史萊姆暱稱", value=nickname, max_chars=16, key=f"nickname_{current['name']}")\n            save_col, cancel_col = st.columns(2)\n            with save_col:\n                if st.button("儲存名字", type="primary", use_container_width=True, key=f"save_nickname_{current['theme']}"):\n                    st.session_state.slime_nicknames[current["name"]] = new_nickname.strip() or current["name"].replace("史萊姆", "")\n                    st.session_state.slime_name_editing = False\n                    st.rerun()\n            with cancel_col:\n                if st.button("取消", use_container_width=True, key=f"cancel_nickname_{current['theme']}"):\n                    st.session_state.slime_name_editing = False\n                    st.rerun()\n\n'''
if old_input not in text:
    raise RuntimeError('nickname input anchor not found')
text = text.replace(old_input, new_input, 1)

# Put the edit button visually directly under the badges and before species information.
# The companion HTML closes before Streamlit can embed the button, so make the species line
# read naturally without duplicating the nickname and keep the button immediately after panel.
# Also remove all series labels from catalog cards.
old_meta = '''                        f'<div class="catalog-card-meta"><span>{item["family"] if not mystery else "神秘系列"}</span>'\n                        f'<span>{("Lv." + str(card_progress["level"]) + " · 🧩 " + str(card_progress.get("fragments", 0))) if is_owned else "🔒 尚未獲得"}</span></div>',\n'''
new_meta = '''                        f'<div class="catalog-card-meta"><span>{("Lv." + str(card_progress["level"]) + " · 🧩 " + str(card_progress.get("fragments", 0))) if is_owned else "🔒 尚未獲得"}</span></div>',\n'''
if old_meta not in text:
    raise RuntimeError('catalog meta anchor not found')
text = text.replace(old_meta, new_meta, 1)

# Catalog metadata no longer needs space-between for two columns.
text = text.replace(
    '.catalog-card-meta { color:#789083; font-size:.78rem; display:flex; justify-content:space-between; gap:.5rem;',
    '.catalog-card-meta { color:#789083; font-size:.78rem; display:flex; justify-content:flex-end; gap:.5rem;',
    1,
)

# Rebuild achievements without opacity on the entire card.
old_ach = '''    cols = st.columns(3)\n    for i, (aid, icon, title, desc, reward) in enumerate(ACHIEVEMENTS):\n        style = "opacity:1" if aid in unlocked else "filter:grayscale(.8);opacity:.55"\n        status = "已解鎖" if aid in unlocked else "尚未解鎖"\n        with cols[i % 3]:\n            st.markdown(f'<div style="{style};background:white;border:1px solid #dfebe4;border-radius:22px;padding:1rem;min-height:150px"><div style="font-size:2rem">{icon}</div><div class="card-title">{title}</div><div class="muted">{desc}</div><div style="margin-top:.6rem;font-weight:850">{status} · {reward}</div></div><br>', unsafe_allow_html=True)\n'''
new_ach = '''    cols = st.columns(3)\n    for i, (aid, icon, title, desc, reward) in enumerate(ACHIEVEMENTS):\n        unlocked_now = aid in unlocked\n        status = "已解鎖" if unlocked_now else "尚未解鎖"\n        card_class = "achievement-card" if unlocked_now else "achievement-card locked"\n        with cols[i % 3]:\n            st.markdown(\n                f'<div class="{card_class}"><div class="achievement-icon">{icon}</div>'\n                f'<div class="achievement-title">{title}</div>'\n                f'<div class="achievement-desc">{desc}</div>'\n                f'<div class="achievement-status">{status} · {reward}</div></div>',\n                unsafe_allow_html=True,\n            )\n'''
if old_ach not in text:
    raise RuntimeError('achievement block anchor not found')
text = text.replace(old_ach, new_ach, 1)

path.write_text(text, encoding='utf-8')
print('fixed slime nickname, series labels, rarity text, and achievements contrast')
