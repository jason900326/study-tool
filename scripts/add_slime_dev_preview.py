from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

# Add session-only developer preview state.
state_anchor = '    "slime_name_editing": False,\n'
if '    "slime_dev_preview": False,\n' not in text:
    if state_anchor not in text:
        raise RuntimeError('slime_name_editing state anchor not found')
    text = text.replace(state_anchor, state_anchor + '    "slime_dev_preview": False,\n', 1)

# Remove the explanatory sentence from the catalog header and add a developer preview toggle.
old_summary = '''    st.markdown(\n        f'<div class="catalog-summary"><div><div class="section-title" style="margin-bottom:.15rem">史萊姆圖鑑</div>'\n        f'<div class="catalog-count">已收集 {len(owned)} / {len(SLIME_CATALOG)} 隻</div></div>'\n        '<div class="catalog-count">N / R 未獲得仍可預覽 · SR / SSR 保持神秘</div></div>',\n        unsafe_allow_html=True,\n    )\n\n    filters = ["全部", "N", "R", "SR", "SSR", "限定"]\n'''
new_summary = '''    st.markdown(\n        f'<div class="catalog-summary"><div><div class="section-title" style="margin-bottom:.15rem">史萊姆圖鑑</div>'\n        f'<div class="catalog-count">已收集 {len(owned)} / {len(SLIME_CATALOG)} 隻</div></div></div>',\n        unsafe_allow_html=True,\n    )\n\n    dev_preview = st.toggle(\n        "🛠️ 開發者預覽",\n        value=bool(st.session_state.slime_dev_preview),\n        key="slime_dev_preview_toggle",\n        help="只解除圖鑑顯示限制，不會把未獲得史萊姆加入收藏。",\n    )\n    st.session_state.slime_dev_preview = bool(dev_preview)\n    if dev_preview:\n        st.caption("開發者預覽中：所有普通卡池史萊姆會顯示完整造型與名稱，但持有狀態不變。")\n\n    filters = ["全部", "N", "R", "SR", "SSR", "限定"]\n'''
if old_summary not in text:
    raise RuntimeError('catalog summary anchor not found')
text = text.replace(old_summary, new_summary, 1)

# Reveal full art/name/tagline in developer preview while preserving actual ownership.
old_logic = '''            is_owned = item["name"] in owned\n            is_selected = item["name"] == st.session_state.selected_slime\n            mystery = (item["rarity"] in ("SR", "SSR")) and not is_owned\n            shown_name = "???" if mystery else item["name"]\n            tagline = "抽到後才會揭曉它的真面目。" if mystery else item["tagline"]\n            card_progress = get_slime_progress(item["name"]) if is_owned else None\n'''
new_logic = '''            is_owned = item["name"] in owned\n            is_selected = item["name"] == st.session_state.selected_slime\n            preview_reveal = bool(st.session_state.slime_dev_preview) and not is_owned\n            mystery = (item["rarity"] in ("SR", "SSR")) and not is_owned and not preview_reveal\n            shown_name = "???" if mystery else item["name"]\n            tagline = "抽到後才會揭曉它的真面目。" if mystery else item["tagline"]\n            card_progress = get_slime_progress(item["name"]) if is_owned else None\n'''
if old_logic not in text:
    raise RuntimeError('catalog display logic anchor not found')
text = text.replace(old_logic, new_logic, 1)

old_art = '''                        f'<div class="catalog-art-shell">{slime_avatar_markup(item, size="card", locked=not is_owned, mystery=mystery, selected=is_selected)}</div>'\n'''
new_art = '''                        f'<div class="catalog-art-shell">{slime_avatar_markup(item, size="card", locked=(not is_owned and not preview_reveal), mystery=mystery, selected=is_selected)}</div>'\n'''
if old_art not in text:
    raise RuntimeError('catalog art anchor not found')
text = text.replace(old_art, new_art, 1)

old_meta = '''                        f'<div class="catalog-card-meta"><span>{("Lv." + str(card_progress["level"]) + " · 🧩 " + str(card_progress.get("fragments", 0))) if is_owned else "🔒 尚未獲得"}</span></div>',\n'''
new_meta = '''                        f'<div class="catalog-card-meta"><span>{("Lv." + str(card_progress["level"]) + " · 🧩 " + str(card_progress.get("fragments", 0))) if is_owned else ("🛠️ 開發預覽" if preview_reveal else "🔒 尚未獲得")}</span></div>',\n'''
if old_meta not in text:
    raise RuntimeError('catalog card meta anchor not found')
text = text.replace(old_meta, new_meta, 1)

old_button = '''                    else:\n                        st.button("🔒 尚未獲得", disabled=True, use_container_width=True, key=f"slime_locked_{item['theme']}_{chosen_filter}")\n'''
new_button = '''                    else:\n                        locked_label = "🛠️ 預覽中" if preview_reveal else "🔒 尚未獲得"\n                        st.button(locked_label, disabled=True, use_container_width=True, key=f"slime_locked_{item['theme']}_{chosen_filter}")\n'''
if old_button not in text:
    raise RuntimeError('catalog locked button anchor not found')
text = text.replace(old_button, new_button, 1)

path.write_text(text, encoding='utf-8')
print('added developer preview and removed catalog explainer')
