from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

# ------------------------------------------------------------------
# Session state: per-slime progress, nicknames, and collection filter.
# ------------------------------------------------------------------
state_anchor = '    "focus_last_duration_minutes": 25,\n'
state_add = state_anchor + '''    "slime_collection_filter": "全部",\n    "slime_progress": {"青蘋果史萊姆": {"level": 4, "exp": 72, "fragments": 0}},\n    "slime_nicknames": {"青蘋果史萊姆": "Medi"},\n'''
if '    "slime_collection_filter": "全部",\n' not in text:
    if state_anchor not in text:
        raise RuntimeError('state anchor not found')
    text = text.replace(state_anchor, state_add, 1)

# ------------------------------------------------------------------
# Replace the old prototype pool with the 11-slime catalog discussed.
# Rates are intentionally provisional until the dedicated gacha pass.
# ------------------------------------------------------------------
old_pool = '''GACHA_POOL = [\n    {"name": "青蘋果史萊姆", "rarity": "N", "emoji": "🟢", "weight": 35},\n    {"name": "薄荷史萊姆", "rarity": "N", "emoji": "🟩", "weight": 35},\n    {"name": "藍莓史萊姆", "rarity": "R", "emoji": "🔵", "weight": 14},\n    {"name": "葡萄史萊姆", "rarity": "R", "emoji": "🟣", "weight": 11},\n    {"name": "黃金史萊姆", "rarity": "SSR", "emoji": "🟡", "weight": 4},\n    {"name": "星空史萊姆", "rarity": "SSR", "emoji": "🌌", "weight": 1},\n]\n'''
new_pool = '''SLIME_CATALOG = [\n    {"name": "青蘋果史萊姆", "rarity": "N", "family": "水果系列", "mark": "🍃", "theme": "apple", "gradient": "linear-gradient(145deg,#a9efad,#47c977)", "tagline": "MedSlime 的品牌夥伴，清爽又充滿活力。", "weight": 15},\n    {"name": "葡萄史萊姆", "rarity": "N", "family": "水果系列", "mark": "●", "theme": "grape", "gradient": "linear-gradient(145deg,#d9b0f1,#8f59bd)", "tagline": "圓滾滾又有彈性，身上帶著葡萄般的光澤。", "weight": 15},\n    {"name": "草莓史萊姆", "rarity": "N", "family": "水果系列", "mark": "✦", "theme": "strawberry", "gradient": "linear-gradient(145deg,#ffb0b8,#ed6672)", "tagline": "活潑愛笑，身體散著像草莓籽的小亮點。", "weight": 15},\n    {"name": "檸檬史萊姆", "rarity": "N", "family": "水果系列", "mark": "🍃", "theme": "lemon", "gradient": "linear-gradient(145deg,#fff397,#ebcf42)", "tagline": "酸酸亮亮，總是一副精神很好的樣子。", "weight": 15},\n    {"name": "牛奶史萊姆", "rarity": "R", "family": "特殊食物系列", "mark": "◌", "theme": "milk", "gradient": "linear-gradient(145deg,#fffdf5,#e9e7df)", "tagline": "像奶凍一樣柔軟，帶著溫柔的霧面光澤。", "weight": 8.34},\n    {"name": "蜂蜜史萊姆", "rarity": "R", "family": "特殊食物系列", "mark": "⌁", "theme": "honey", "gradient": "linear-gradient(145deg,#ffe58b,#d99425)", "tagline": "琥珀色的身體慢慢流動，甜甜又黏呼呼。", "weight": 8.33},\n    {"name": "咖啡史萊姆", "rarity": "R", "family": "特殊食物系列", "mark": "☕", "theme": "coffee", "gradient": "linear-gradient(145deg,#d6a06f,#795039)", "tagline": "帶著咖啡香氣的沉穩夥伴，頭頂有奶泡般的紋路。", "weight": 8.33},\n    {"name": "雲朵史萊姆", "rarity": "SR", "family": "自然系列", "mark": "☁", "theme": "cloud", "gradient": "linear-gradient(145deg,#ffffff,#bcdcf1)", "tagline": "輕飄飄又蓬鬆，像把一小朵雲抱在懷裡。", "weight": 5},\n    {"name": "海洋史萊姆", "rarity": "SR", "family": "自然系列", "mark": "〰", "theme": "ocean", "gradient": "linear-gradient(145deg,#7de4e5,#367fd0)", "tagline": "透明身體裡像藏著海浪，安靜地一波一波流動。", "weight": 5},\n    {"name": "晚霞史萊姆", "rarity": "SSR", "family": "夢幻系列", "mark": "✦", "theme": "sunset", "gradient": "linear-gradient(145deg,#ffd36a 0%,#ff8c8d 45%,#b66fe5 100%)", "tagline": "橘粉紫的天空在身體裡流動，邊緣帶著淡金光。", "weight": 2.5},\n    {"name": "星空史萊姆", "rarity": "SSR", "family": "夢幻系列", "mark": "✧", "theme": "starry", "gradient": "linear-gradient(145deg,#5050a5 0%,#242655 55%,#10172e 100%)", "tagline": "深色身體裡閃著星點，像裝著一小片夜空。", "weight": 2.5},\n]\n\nSLIME_BY_NAME = {item["name"]: item for item in SLIME_CATALOG}\nGACHA_POOL = SLIME_CATALOG\n'''
if old_pool not in text:
    raise RuntimeError('old gacha pool not found')
text = text.replace(old_pool, new_pool, 1)

# ------------------------------------------------------------------
# Visual helpers: catalog placeholder art + per-slime progress.
# ------------------------------------------------------------------
old_helper = '''def selected_slime_background():\n    palettes = {\n        "青蘋果史萊姆": "linear-gradient(145deg,#9bedad,#48c878)",\n        "薄荷史萊姆": "linear-gradient(145deg,#b6f2d7,#58cba1)",\n        "藍莓史萊姆": "linear-gradient(145deg,#a9d8ff,#5798e6)",\n        "葡萄史萊姆": "linear-gradient(145deg,#d9b7ff,#9a67d8)",\n        "黃金史萊姆": "linear-gradient(145deg,#ffe78b,#e6b83f)",\n        "星空史萊姆": "linear-gradient(145deg,#8e8eea,#514d9d)",\n    }\n    return palettes.get(st.session_state.selected_slime, palettes["青蘋果史萊姆"])\n'''
new_helper = '''def slime_data(name):\n    return SLIME_BY_NAME.get(name, SLIME_BY_NAME["青蘋果史萊姆"])\n\n\ndef get_slime_progress(name):\n    progress = st.session_state.slime_progress\n    if name not in progress:\n        progress[name] = {"level": 1, "exp": 0, "fragments": 0}\n    return progress[name]\n\n\ndef get_slime_nickname(name):\n    nicknames = st.session_state.slime_nicknames\n    if name not in nicknames:\n        nicknames[name] = name.replace("史萊姆", "")\n    return nicknames[name]\n\n\ndef selected_slime_background():\n    return slime_data(st.session_state.selected_slime)["gradient"]\n\n\ndef slime_avatar_markup(item, size="card", locked=False, mystery=False, selected=False):\n    classes = ["catalog-slime", f"catalog-slime-{size}", f"theme-{item['theme']}"]\n    if locked:\n        classes.append("locked")\n    if mystery:\n        classes.append("mystery")\n    if selected:\n        classes.append("selected")\n    gradient = "linear-gradient(145deg,#66706b,#252d29)" if mystery else item["gradient"]\n    mark = "?" if mystery else item.get("mark", "")\n    face = "" if mystery else '<span class="catalog-eye eye-left"></span><span class="catalog-eye eye-right"></span><span class="catalog-mouth"></span>'\n    lock = '<span class="catalog-lock">🔒</span>' if locked else ""\n    return (\n        f'<div class="{" ".join(classes)}" style="background:{gradient}">'\n        f'<span class="catalog-mark">{mark}</span>{face}{lock}</div>'\n    )\n'''
if old_helper not in text:
    raise RuntimeError('selected slime helper anchor not found')
text = text.replace(old_helper, new_helper, 1)

# ------------------------------------------------------------------
# Home hero now reads the selected slime's own level/EXP.
# ------------------------------------------------------------------
old_home_start = '''def home():\n    topbar()\n    left, right = st.columns([1.35, 1], gap="large", vertical_alignment="center")\n'''
new_home_start = '''def home():\n    topbar()\n    companion_progress = get_slime_progress(st.session_state.selected_slime)\n    companion_nickname = get_slime_nickname(st.session_state.selected_slime)\n    left, right = st.columns([1.35, 1], gap="large", vertical_alignment="center")\n'''
if old_home_start not in text:
    raise RuntimeError('home start anchor not found')
text = text.replace(old_home_start, new_home_start, 1)
old_home_card = '''        st.markdown('<div class="home-slime-card">' + slime_markup() + f'<div class="home-slime-label">{st.session_state.slime_name} · Lv.{st.session_state.player_level}</div><div class="home-xp"><div class="home-xp-fill" style="width:{st.session_state.player_exp}%"></div></div><div class="muted">{st.session_state.player_exp} / 100 EXP · {st.session_state.selected_slime}</div></div>', unsafe_allow_html=True)\n'''
new_home_card = '''        companion_item = slime_data(st.session_state.selected_slime)\n        st.markdown('<div class="home-slime-card">' + slime_avatar_markup(companion_item, size="home") + f'<div class="home-slime-label">{html.escape(companion_nickname)} · Lv.{companion_progress["level"]}</div><div class="home-xp"><div class="home-xp-fill" style="width:{min(100, companion_progress["exp"])}%"></div></div><div class="muted">{companion_progress["exp"]} / 100 EXP · {st.session_state.selected_slime}</div></div>', unsafe_allow_html=True)\n'''
if old_home_card not in text:
    raise RuntimeError('home slime card anchor not found')
text = text.replace(old_home_card, new_home_card, 1)

# ------------------------------------------------------------------
# Collection UI styles.
# ------------------------------------------------------------------
css_anchor = '    .slime { width:178px; height:142px; margin:0 auto 1rem;'
css = r'''    /* My Slime collection / catalog */
    .slime-page-header { margin:.35rem 0 1rem; }
    .slime-hub-actions { margin:.4rem 0 1rem; }
    .companion-panel { display:flex; gap:1.7rem; align-items:center; background:linear-gradient(135deg,#eefaf3,#ffffff 62%,#edf8fc); border:1px solid #d7eadf; border-radius:30px; padding:1.55rem 1.7rem; box-shadow:0 16px 38px rgba(30,82,51,.065); margin:.5rem 0 1.25rem; overflow:hidden; }
    .companion-art { width:220px; min-width:220px; display:flex; justify-content:center; align-items:center; }
    .companion-info { flex:1; min-width:0; }
    .companion-topline { display:flex; flex-wrap:wrap; gap:.45rem; align-items:center; margin-bottom:.35rem; }
    .rarity-chip,.family-chip,.owned-chip { display:inline-flex; align-items:center; min-height:27px; padding:.2rem .55rem; border-radius:999px; font-size:.76rem; font-weight:950; }
    .rarity-chip { background:#173b2b; color:#fff; }
    .rarity-chip.rarity-R { background:#4d77bd; }
    .rarity-chip.rarity-SR { background:#8b63bc; }
    .rarity-chip.rarity-SSR { background:linear-gradient(90deg,#9d6bc3,#d88c61); }
    .family-chip { background:#fff; border:1px solid #dceae2; color:#627d6f; }
    .owned-chip { background:#e7f8ed; color:#228a51; }
    .companion-name { color:#173b2b; font-size:1.65rem; font-weight:950; letter-spacing:-.03em; margin:.2rem 0 .25rem; }
    .companion-species { color:#638071; font-size:.9rem; margin-bottom:.8rem; }
    .companion-level-row { display:flex; align-items:center; justify-content:space-between; gap:1rem; color:#285841; font-weight:900; margin:.2rem 0 .35rem; }
    .companion-xp { width:100%; height:10px; border-radius:999px; overflow:hidden; background:#dce9df; }
    .companion-xp > span { display:block; height:100%; border-radius:inherit; background:linear-gradient(90deg,#58d28a,#42bda4); }
    .companion-meta { display:flex; flex-wrap:wrap; gap:.8rem; color:#71887b; font-size:.84rem; margin-top:.65rem; }
    .catalog-summary { display:flex; justify-content:space-between; gap:1rem; align-items:end; flex-wrap:wrap; margin:1.35rem 0 .35rem; }
    .catalog-count { color:#6f8679; font-size:.88rem; font-weight:750; }
    [class*="st-key-slime_catalog_card_"] { background:rgba(255,255,255,.96); border:1px solid #dceae2; border-radius:22px; padding:1rem; min-height:350px; box-shadow:0 10px 25px rgba(31,83,53,.045); margin-bottom:.8rem; }
    [class*="st-key-slime_catalog_card_"]:has(.catalog-card-selected) { border-color:#77d69d; box-shadow:0 0 0 3px rgba(49,201,120,.1),0 12px 26px rgba(31,83,53,.05); }
    .catalog-card-selected { height:0; overflow:hidden; }
    .catalog-art-shell { min-height:145px; display:flex; align-items:center; justify-content:center; position:relative; }
    .catalog-card-head { display:flex; justify-content:space-between; gap:.4rem; align-items:center; margin-top:.35rem; }
    .catalog-card-name { color:#1c4332; font-size:1.03rem; font-weight:950; line-height:1.35; }
    .catalog-card-tagline { color:#70877a; font-size:.82rem; line-height:1.5; min-height:50px; margin:.55rem 0 .65rem; }
    .catalog-card-meta { color:#789083; font-size:.78rem; display:flex; justify-content:space-between; gap:.5rem; border-top:1px solid #edf2ef; padding-top:.55rem; margin-top:.35rem; }
    .catalog-lock-copy { color:#84968c; font-size:.8rem; font-weight:850; }
    .catalog-mystery-copy { text-align:center; color:#687b71; font-size:.83rem; line-height:1.45; min-height:50px; margin:.55rem 0 .65rem; }
    .limited-empty { border:1px dashed #cbded2; background:linear-gradient(135deg,#fbfdfc,#f2f8f5); border-radius:24px; padding:2rem 1.3rem; text-align:center; color:#627b6d; margin:.75rem 0; }
    .limited-lock { font-size:2.2rem; margin-bottom:.45rem; }
    .art-placeholder-note { color:#8aa095; font-size:.75rem; margin-top:.45rem; }

    .catalog-slime { position:relative; border-radius:50% 50% 40% 40%/62% 62% 38% 38%; box-shadow:inset -10px -13px 0 rgba(25,70,45,.075),0 12px 22px rgba(39,110,73,.12); }
    .catalog-slime-card { width:112px; height:88px; }
    .catalog-slime-home { width:150px; height:118px; margin:0 auto .8rem; animation:slimeBounce 2.4s ease-in-out infinite; }
    .catalog-slime-hero { width:176px; height:138px; animation:slimeBounce 2.2s ease-in-out infinite; }
    .catalog-slime::after { content:""; position:absolute; left:20%; top:14%; width:23%; height:12%; border-radius:50%; background:rgba(255,255,255,.42); transform:rotate(-22deg); }
    .catalog-eye { position:absolute; top:43%; width:8%; height:12%; border-radius:50%; background:#173b2b; z-index:3; }
    .eye-left { left:31%; } .eye-right { right:31%; }
    .catalog-mouth { position:absolute; left:41%; top:61%; width:19%; height:10%; border-bottom:3px solid #173b2b; border-radius:0 0 50% 50%; z-index:3; }
    .catalog-mark { position:absolute; left:50%; top:-18%; transform:translateX(-50%); z-index:5; font-size:1.3rem; font-weight:950; filter:drop-shadow(0 3px 4px rgba(35,70,50,.1)); }
    .catalog-slime-hero .catalog-mark { font-size:1.8rem; }
    .catalog-lock { position:absolute; right:-10px; top:-9px; width:32px; height:32px; display:flex; align-items:center; justify-content:center; border-radius:50%; background:#fff; border:1px solid #d8e5dd; box-shadow:0 4px 12px rgba(36,67,50,.12); font-size:.9rem; z-index:8; }
    .catalog-slime.locked:not(.mystery) { filter:saturate(.42); opacity:.64; box-shadow:inset -10px -13px 0 rgba(25,70,45,.06),0 8px 16px rgba(39,110,73,.07); }
    .catalog-slime.mystery { filter:saturate(.15); opacity:.78; box-shadow:0 10px 22px rgba(22,35,29,.12); }
    .catalog-slime.mystery::after { opacity:.08; }
    .catalog-slime.mystery .catalog-mark { top:34%; color:#fff; font-size:2rem; opacity:.62; }
    .theme-strawberry { background-image:radial-gradient(circle at 28% 28%,rgba(255,235,165,.7) 0 2px,transparent 3px),radial-gradient(circle at 68% 52%,rgba(255,235,165,.65) 0 2px,transparent 3px) !important; }
    .theme-honey::before { content:""; position:absolute; right:9%; bottom:-8%; width:22%; height:26%; border-radius:0 0 50% 50%; background:rgba(199,126,26,.46); }
    .theme-coffee::before { content:""; position:absolute; left:29%; top:5%; width:45%; height:16%; border-radius:50%; border-top:4px solid rgba(255,239,208,.78); transform:rotate(-8deg); }
    .theme-cloud { border-radius:48% 52% 37% 43%/58% 61% 39% 42%; box-shadow:-20px 7px 0 -8px rgba(228,241,248,.95),20px 7px 0 -8px rgba(213,235,247,.95),0 12px 22px rgba(70,110,130,.1); }
    .theme-ocean::before { content:"〰"; position:absolute; left:17%; right:17%; bottom:8%; color:rgba(255,255,255,.62); font-size:2rem; text-align:center; line-height:1; }
    .theme-sunset::before,.theme-starry::before { content:"✦  ·  ✧"; position:absolute; left:16%; top:17%; color:rgba(255,255,255,.68); letter-spacing:.35rem; font-size:.8rem; }
    .theme-starry::before { content:"✦ · ✧ ·"; top:21%; color:rgba(255,235,174,.78); }

'''
if '.companion-panel {' not in text:
    if css_anchor not in text:
        raise RuntimeError('CSS slime anchor not found')
    text = text.replace(css_anchor, css + css_anchor, 1)

mobile_anchor = '        .pill { min-height:31px; padding:.23rem .32rem; font-size:.67rem; box-shadow:none; }\n'
mobile_add = mobile_anchor + '''        .companion-panel { flex-direction:column; text-align:center; gap:.75rem; padding:1.25rem 1rem; }\n        .companion-art { width:100%; min-width:0; }\n        .companion-topline,.companion-meta { justify-content:center; }\n        .companion-name { font-size:1.4rem; }\n        .catalog-slime-hero { width:145px; height:114px; }\n        [class*="st-key-slime_catalog_card_"] { min-height:330px; }\n'''
if '        .companion-panel { flex-direction:column;' not in text:
    if mobile_anchor not in text:
        raise RuntimeError('mobile CSS anchor not found')
    text = text.replace(mobile_anchor, mobile_add, 1)

# ------------------------------------------------------------------
# Replace the old My Slime test page with the real collection UI.
# ------------------------------------------------------------------
old_page = '''def slime_page():\n    topbar()\n    render_back_button("返回首頁", "home", "back_slime")\n    st.markdown("## 🐾 我的史萊姆")\n    gacha_col, achievement_col = st.columns(2)\n    with gacha_col:\n        if st.button("🎰 抽卡", use_container_width=True, key="slime_to_gacha"):\n            goto("gacha")\n    with achievement_col:\n        if st.button("🏆 成就", use_container_width=True, key="slime_to_achievements"):\n            goto("achievements")\n    left, right = st.columns([1, 1.35], gap="large")\n    with left:\n        st.markdown('<div style="text-align:center;padding:1.2rem;background:white;border:1px solid #dfebe4;border-radius:24px">' + slime_markup() + '</div>', unsafe_allow_html=True)\n        st.session_state.slime_name = st.text_input("史萊姆名字", value=st.session_state.slime_name, max_chars=16)\n    with right:\n        st.markdown("### 收藏")\n        for slime in st.session_state.collection:\n            if st.button(("✅ " if slime == st.session_state.selected_slime else "🟢 ") + slime, key=f"slime_{slime}", use_container_width=True):\n                st.session_state.selected_slime = slime\n                st.rerun()\n'''
new_page = r'''def slime_page():
    topbar()
    render_back_button("返回首頁", "home", "back_slime")

    # Keep legacy sessions valid after removing old prototype species.
    catalog_names = {item["name"] for item in SLIME_CATALOG}
    if "青蘋果史萊姆" not in st.session_state.collection:
        st.session_state.collection.append("青蘋果史萊姆")
    if st.session_state.selected_slime not in catalog_names or st.session_state.selected_slime not in st.session_state.collection:
        st.session_state.selected_slime = "青蘋果史萊姆"

    owned = {name for name in st.session_state.collection if name in catalog_names}
    current = slime_data(st.session_state.selected_slime)
    progress = get_slime_progress(current["name"])
    nickname = get_slime_nickname(current["name"])

    st.markdown(
        '<div class="slime-page-header"><div class="eyebrow">MY SLIMES</div>'
        '<div class="hero-title" style="font-size:2.05rem">我的史萊姆</div>'
        '<div class="hero-copy">收藏、培養並選擇今天陪你學習的史萊姆。每一隻都有自己的 Lv. 與 EXP。</div></div>',
        unsafe_allow_html=True,
    )

    action_left, action_right = st.columns(2)
    with action_left:
        if st.button("🎰 前往抽卡", use_container_width=True, key="slime_to_gacha"):
            goto("gacha")
    with action_right:
        if st.button("🏆 查看成就", use_container_width=True, key="slime_to_achievements"):
            goto("achievements")

    rarity_class = f"rarity-{current['rarity']}"
    st.markdown(
        '<div class="companion-panel">'
        f'<div class="companion-art">{slime_avatar_markup(current, size="hero", selected=True)}</div>'
        '<div class="companion-info">'
        f'<div class="companion-topline"><span class="rarity-chip {rarity_class}">{current["rarity"]}</span>'
        f'<span class="family-chip">{current["family"]}</span><span class="owned-chip">✓ 陪伴中</span></div>'
        f'<div class="companion-name">{html.escape(nickname)}</div>'
        f'<div class="companion-species">{current["name"]} · {current["tagline"]}</div>'
        f'<div class="companion-level-row"><span>Lv.{progress["level"]}</span><span>{progress["exp"]} / 100 EXP</span></div>'
        f'<div class="companion-xp"><span style="width:{min(100, int(progress["exp"]))}%"></span></div>'
        f'<div class="companion-meta"><span>🧩 專屬碎片 {progress.get("fragments", 0)}</span><span>🎨 三階段成長：規劃中</span><span>🎩 裝扮：下一階段</span></div>'
        '<div class="art-placeholder-note">目前角色為介面占位造型；正式美術會在角色設計定稿後替換。</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    new_nickname = st.text_input("史萊姆暱稱", value=nickname, max_chars=16, key=f"nickname_{current['name']}")
    if new_nickname != nickname:
        st.session_state.slime_nicknames[current["name"]] = new_nickname.strip() or current["name"].replace("史萊姆", "")

    st.markdown(
        f'<div class="catalog-summary"><div><div class="section-title" style="margin-bottom:.15rem">史萊姆圖鑑</div>'
        f'<div class="catalog-count">已收集 {len(owned)} / {len(SLIME_CATALOG)} 隻</div></div>'
        '<div class="catalog-count">N / R 未獲得仍可預覽 · SR / SSR 保持神秘</div></div>',
        unsafe_allow_html=True,
    )

    filters = ["全部", "N", "R", "SR", "SSR", "限定"]
    chosen_filter = st.radio(
        "圖鑑篩選",
        filters,
        index=filters.index(st.session_state.slime_collection_filter) if st.session_state.slime_collection_filter in filters else 0,
        horizontal=True,
        label_visibility="collapsed",
        key="slime_catalog_filter_widget",
    )
    st.session_state.slime_collection_filter = chosen_filter

    if chosen_filter == "限定":
        st.markdown(
            '<div class="limited-empty"><div class="limited-lock">🏆🔒</div>'
            '<div class="card-title" style="font-size:1.15rem">限定史萊姆</div>'
            '<div style="margin-top:.45rem">限定史萊姆不會出現在一般卡池，會和特殊成就直接連動。</div>'
            '<div class="muted" style="margin-top:.5rem">例如：完成整份國考並達成指定分數後解鎖「學霸史萊姆」。角色與條件會在成就系統階段正式加入。</div></div>',
            unsafe_allow_html=True,
        )
        return

    visible_items = SLIME_CATALOG if chosen_filter == "全部" else [item for item in SLIME_CATALOG if item["rarity"] == chosen_filter]
    for row_start in range(0, len(visible_items), 3):
        row = visible_items[row_start:row_start + 3]
        cols = st.columns(3, gap="medium")
        for offset, (col, item) in enumerate(zip(cols, row)):
            index = row_start + offset
            is_owned = item["name"] in owned
            is_selected = item["name"] == st.session_state.selected_slime
            mystery = (item["rarity"] in ("SR", "SSR")) and not is_owned
            shown_name = "???" if mystery else item["name"]
            tagline = "抽到後才會揭曉它的真面目。" if mystery else item["tagline"]
            card_progress = get_slime_progress(item["name"]) if is_owned else None
            with col:
                with st.container(key=f"slime_catalog_card_{chosen_filter}_{index}"):
                    if is_selected:
                        st.markdown('<div class="catalog-card-selected"></div>', unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="catalog-art-shell">{slime_avatar_markup(item, size="card", locked=not is_owned, mystery=mystery, selected=is_selected)}</div>'
                        f'<div class="catalog-card-head"><div class="catalog-card-name">{shown_name}</div>'
                        f'<span class="rarity-chip rarity-{item["rarity"]}">{item["rarity"]}</span></div>'
                        f'<div class="catalog-card-tagline">{tagline}</div>'
                        f'<div class="catalog-card-meta"><span>{item["family"] if not mystery else "神秘系列"}</span>'
                        f'<span>{("Lv." + str(card_progress["level"]) + " · 🧩 " + str(card_progress.get("fragments", 0))) if is_owned else "🔒 尚未獲得"}</span></div>',
                        unsafe_allow_html=True,
                    )
                    if is_selected:
                        st.button("✓ 陪伴中", disabled=True, use_container_width=True, key=f"slime_selected_{index}_{chosen_filter}")
                    elif is_owned:
                        if st.button("設為陪伴", type="primary", use_container_width=True, key=f"slime_select_{item['theme']}_{chosen_filter}"):
                            st.session_state.selected_slime = item["name"]
                            get_slime_progress(item["name"])
                            get_slime_nickname(item["name"])
                            st.rerun()
                    else:
                        st.button("🔒 尚未獲得", disabled=True, use_container_width=True, key=f"slime_locked_{item['theme']}_{chosen_filter}")
'''
if old_page not in text:
    raise RuntimeError('old slime page block not found')
text = text.replace(old_page, new_page, 1)

# ------------------------------------------------------------------
# Keep the still-prototype gacha consistent: duplicate -> fragments + coins.
# ------------------------------------------------------------------
old_gacha_caption = '    st.caption("1 張抽卡券 = 1 次召喚 · N 70% · R 25% · SSR 5%")\n'
new_gacha_caption = '    st.caption("史萊姆池 · 目前機率暫定 N 60% / R 25% / SR 10% / SSR 5%；正式卡池會在下一階段調整。")\n'
if old_gacha_caption in text:
    text = text.replace(old_gacha_caption, new_gacha_caption, 1)

old_dup = '''        duplicate = result["name"] in st.session_state.collection\n        if duplicate:\n            st.session_state.coins += 50 if result["rarity"] == "N" else 120 if result["rarity"] == "R" else 300\n        else:\n            st.session_state.collection.append(result["name"])\n        st.session_state.last_gacha = {**result, "duplicate": duplicate}\n'''
new_dup = '''        duplicate = result["name"] in st.session_state.collection\n        fragments = 0\n        refund = 0\n        if duplicate:\n            fragments = {"N": 1, "R": 2, "SR": 4, "SSR": 8}[result["rarity"]]\n            refund = {"N": 10, "R": 20, "SR": 40, "SSR": 80}[result["rarity"]]\n            get_slime_progress(result["name"])["fragments"] += fragments\n            st.session_state.coins += refund\n        else:\n            st.session_state.collection.append(result["name"])\n            get_slime_progress(result["name"])\n            get_slime_nickname(result["name"])\n        st.session_state.last_gacha = {**result, "duplicate": duplicate, "fragments": fragments, "refund": refund}\n'''
if old_dup not in text:
    raise RuntimeError('gacha duplicate block not found')
text = text.replace(old_dup, new_dup, 1)

old_msg = '        msg = "重複獲得，已轉換成金幣" if result["duplicate"] else "NEW！已加入收藏"\n'
new_msg = '        msg = (f"重複獲得 · +{result.get(\'fragments\', 0)} 專屬碎片 · +{result.get(\'refund\', 0)} 🪙" if result["duplicate"] else "NEW！已加入收藏")\n'
if old_msg not in text:
    raise RuntimeError('gacha result message anchor not found')
text = text.replace(old_msg, new_msg, 1)

path.write_text(text, encoding='utf-8')
print('rebuilt My Slime collection interface')
