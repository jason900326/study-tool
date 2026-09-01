from pathlib import Path

p = Path('streamlit_app.py')
s = p.read_text(encoding='utf-8')

# 1) Make the gacha page text colors explicit so global Streamlit styles cannot turn them white.
old = '''        .gacha-mvp-title{font-size:1.75rem;font-weight:950;color:#17372a;letter-spacing:-.03em}.gacha-mvp-copy{color:#789083;margin-top:.35rem;line-height:1.55}\n        .gacha-mvp-pity{display:inline-flex;margin-top:.75rem;padding:.35rem .7rem;border-radius:999px;background:#f2f8f4;color:#315b45;font-size:.78rem;font-weight:850}\n'''
new = '''        .gacha-mvp-marker{display:none}.gacha-mvp-title{font-size:1.75rem;font-weight:950;color:#17372a!important;letter-spacing:-.03em}.gacha-mvp-copy{color:#789083!important;margin-top:.35rem;line-height:1.55}\n        [data-testid="stMainBlockContainer"]:has(.gacha-mvp-marker) h1,[data-testid="stMainBlockContainer"]:has(.gacha-mvp-marker) h2,[data-testid="stMainBlockContainer"]:has(.gacha-mvp-marker) h3,[data-testid="stMainBlockContainer"]:has(.gacha-mvp-marker) h4,[data-testid="stMainBlockContainer"]:has(.gacha-mvp-marker) p,[data-testid="stMainBlockContainer"]:has(.gacha-mvp-marker) label{color:#244c39!important}[data-testid="stMainBlockContainer"]:has(.gacha-mvp-marker) [data-testid="stCaptionContainer"] p{color:#789083!important}\n'''
if old not in s:
    raise RuntimeError('gacha css anchor not found')
s = s.replace(old, new, 1)

old = '''    topbar()\n    render_back_button("返回我的史萊姆", "slime", "back_gacha")\n'''
new = '''    topbar()\n    st.markdown('<div class="gacha-mvp-marker"></div>', unsafe_allow_html=True)\n    render_back_button("返回我的史萊姆", "slime", "back_gacha")\n'''
# Only replace inside gacha_page.
gacha_pos = s.index('def gacha_page():')
pos = s.index(old, gacha_pos)
s = s[:pos] + s[pos:].replace(old, new, 1)

# 2) Keep SSR pity logic but hide all pity UI text.
old = '''    pity = int(st.session_state.get("gacha_pity", 0) or 0)\n    today_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")\n'''
new = '''    today_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")\n'''
if old not in s:
    raise RuntimeError('pity variable anchor not found')
s = s.replace(old, new, 1)

old = '''    st.markdown(\n        f'<div class="gacha-mvp-hero"><div class="gacha-mvp-title">🎰 史萊姆召喚</div>'\n        f'<div class="gacha-mvp-copy">測試版：單抽與 10 連都直接顯示結果，暫時沒有翻牌動畫。</div>'\n        f'<div class="gacha-mvp-pity">SSR 保底：{pity} / 100</div></div>',\n        unsafe_allow_html=True,\n    )\n    st.caption("機率：N 32% · R 38% · SR 27% · SSR 3%　｜　所有抽法共用 100 抽 SSR 保底")\n'''
new = '''    st.markdown(\n        '<div class="gacha-mvp-hero"><div class="gacha-mvp-title">🎰 史萊姆召喚</div>'\n        '<div class="gacha-mvp-copy">測試版：單抽與 10 連都直接顯示結果，暫時沒有翻牌動畫。</div></div>',\n        unsafe_allow_html=True,\n    )\n    st.caption("機率：N 32% · R 38% · SR 27% · SSR 3%")\n'''
if old not in s:
    raise RuntimeError('pity display anchor not found')
s = s.replace(old, new, 1)

# 3) After three duplicate pulls (30 fragments), further duplicates refund coins by rarity.
old = '''        duplicate = result["name"] in st.session_state.collection\n        fragments = 0\n        if duplicate:\n            fragments = 10\n            get_slime_progress(result["name"])["fragments"] += 10\n        else:\n            st.session_state.collection.append(result["name"])\n            get_slime_progress(result["name"])\n            get_slime_nickname(result["name"])\n\n        st.session_state.gacha_pity = 0 if result["rarity"] == "SSR" else current_pity + 1\n        return {**result, "duplicate": duplicate, "fragments": fragments, "payment": payment}\n'''
new = '''        duplicate = result["name"] in st.session_state.collection\n        fragments = 0\n        refund = 0\n        if duplicate:\n            progress = get_slime_progress(result["name"])\n            accessory_unlocked = bool(st.session_state.slime_accessories.get(result["name"], False))\n            if accessory_unlocked or int(progress.get("fragments", 0) or 0) >= 30:\n                refund = {"N": 10, "R": 20, "SR": 40, "SSR": 80}[result["rarity"]]\n                st.session_state.coins += refund\n            else:\n                fragments = min(10, 30 - int(progress.get("fragments", 0) or 0))\n                progress["fragments"] += fragments\n        else:\n            st.session_state.collection.append(result["name"])\n            get_slime_progress(result["name"])\n            get_slime_nickname(result["name"])\n\n        st.session_state.gacha_pity = 0 if result["rarity"] == "SSR" else current_pity + 1\n        return {**result, "duplicate": duplicate, "fragments": fragments, "refund": refund, "payment": payment}\n'''
if old not in s:
    raise RuntimeError('duplicate reward anchor not found')
s = s.replace(old, new, 1)

# Single-pull result message.
old = '''        if result.get("duplicate"):\n            message = "重複獲得"\n            sub = f'+10 {html.escape(result["name"])}專屬碎片'\n        else:\n'''
new = '''        if result.get("duplicate"):\n            message = "重複獲得"\n            if result.get("refund", 0):\n                sub = f'專屬飾品碎片已滿 · +{result["refund"]} 🪙'\n            else:\n                sub = f'+{result.get("fragments", 0)} {html.escape(result["name"])}專屬碎片'\n        else:\n'''
if old not in s:
    raise RuntimeError('single result message anchor not found')
s = s.replace(old, new, 1)

# Ten-pull result message.
old = '''                    status = "重複 · +10 碎片" if result.get("duplicate") else "NEW！"\n'''
new = '''                    if result.get("duplicate"):\n                        status = f"重複 · +{result['refund']} 金幣" if result.get("refund", 0) else f"重複 · +{result.get('fragments', 0)} 碎片"\n                    else:\n                        status = "NEW！"\n'''
if old not in s:
    raise RuntimeError('ten result message anchor not found')
s = s.replace(old, new, 1)

# 4) Expanded owned slime cards show the current nickname + pencil and allow renaming.
old = '''                card_class = f'slime-v2-card{"" if owned else " locked"}{" expanded" if detail_open else ""}'\n                st.markdown(\n                    f'<div class="{card_class}">{avatar}<div class="slime-v2-card-name">{html.escape(title)}</div>'\n                    f'<div class="slime-v2-meta">{x["rarity"]} · {"已擁有" if owned else "尚未取得"}</div>{companion_line}{expanded_body}</div>',\n                    unsafe_allow_html=True,\n                )\n'''
new = '''                card_class = f'slime-v2-card{"" if owned else " locked"}{" expanded" if detail_open else ""}'\n                current_nickname = st.session_state.slime_nicknames.get(x["name"], title) if owned else title\n                shown_title = f"{current_nickname} ✏️" if detail_open and owned else title\n                st.markdown(\n                    f'<div class="{card_class}">{avatar}<div class="slime-v2-card-name">{html.escape(shown_title)}</div>'\n                    f'<div class="slime-v2-meta">{x["rarity"]} · {"已擁有" if owned else "尚未取得"}</div>{companion_line}{expanded_body}</div>',\n                    unsafe_allow_html=True,\n                )\n'''
if old not in s:
    raise RuntimeError('slime card title anchor not found')
s = s.replace(old, new, 1)

old = '''                if detail_open and owned:\n                    acc=st.session_state.slime_accessories.setdefault(x["name"],False)\n                    if x["name"]!=st.session_state.selected_slime:\n'''
new = '''                if detail_open and owned:\n                    acc=st.session_state.slime_accessories.setdefault(x["name"],False)\n                    rename_value = st.text_input(\n                        "修改史萊姆名稱",\n                        value=st.session_state.slime_nicknames.get(x["name"], x["name"]),\n                        max_chars=20,\n                        key=f"rename_input_{x['theme']}",\n                    )\n                    if st.button("儲存名稱", use_container_width=True, key=f"rename_save_{x['theme']}"):\n                        cleaned_name = str(rename_value or "").strip()\n                        if cleaned_name:\n                            st.session_state.slime_nicknames[x["name"]] = cleaned_name\n                            st.rerun()\n                    if x["name"]!=st.session_state.selected_slime:\n'''
if old not in s:
    raise RuntimeError('rename control anchor not found')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
print('refined gacha rewards/colors and added slime rename')
