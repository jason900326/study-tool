from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

# Replace topbar CSS that depended on the hamburger-menu column.
old_css = '''    [data-testid="stHorizontalBlock"]:has([class*="st-key-nav_toggle"]) { flex-wrap:nowrap !important; align-items:center !important; gap:.35rem !important; }\n    [data-testid="stHorizontalBlock"]:has([class*="st-key-nav_toggle"]) > div:nth-child(1) { min-width:46px !important; width:46px !important; flex:0 0 46px !important; }\n    [data-testid="stHorizontalBlock"]:has([class*="st-key-nav_toggle"]) > div:nth-child(2) { min-width:145px !important; flex:1 1 auto !important; }\n    [data-testid="stHorizontalBlock"]:has([class*="st-key-nav_toggle"]) > div:nth-child(3) { min-width:0 !important; flex:0 1 auto !important; margin-left:auto !important; }\n    [class*="st-key-nav_toggle"] button { width:42px !important; height:42px !important; min-width:42px !important; min-height:42px !important; padding:0 !important; border:none !important; border-radius:12px !important; background:#17372a !important; color:white !important; box-shadow:0 5px 14px rgba(23,55,42,.15) !important; font-size:1.2rem !important; }\n'''
new_css = '''    [class*="st-key-topbar_shell"] [data-testid="stHorizontalBlock"] { flex-wrap:nowrap !important; align-items:center !important; gap:.35rem !important; }\n    [class*="st-key-topbar_shell"] [data-testid="stHorizontalBlock"] > div:nth-child(1) { min-width:145px !important; flex:1 1 auto !important; }\n    [class*="st-key-topbar_shell"] [data-testid="stHorizontalBlock"] > div:nth-child(2) { min-width:0 !important; flex:0 1 auto !important; margin-left:auto !important; }\n'''
if old_css not in text:
    raise RuntimeError('desktop topbar CSS anchor not found')
text = text.replace(old_css, new_css, 1)

old_mobile = '''        [data-testid="stHorizontalBlock"]:has([class*="st-key-nav_toggle"]) { gap:.18rem !important; }\n        [data-testid="stHorizontalBlock"]:has([class*="st-key-nav_toggle"]) > div:nth-child(1) { min-width:42px !important; width:42px !important; flex:0 0 42px !important; }\n        [data-testid="stHorizontalBlock"]:has([class*="st-key-nav_toggle"]) > div:nth-child(2) { min-width:112px !important; }\n        [class*="st-key-nav_toggle"] button { width:38px !important; height:38px !important; min-width:38px !important; min-height:38px !important; font-size:1.05rem !important; }\n'''
new_mobile = '''        [class*="st-key-topbar_shell"] [data-testid="stHorizontalBlock"] { gap:.18rem !important; }\n        [class*="st-key-topbar_shell"] [data-testid="stHorizontalBlock"] > div:nth-child(1) { min-width:118px !important; }\n        [class*="st-key-topbar_shell"] [data-testid="stHorizontalBlock"] > div:nth-child(2) { min-width:0 !important; }\n'''
if old_mobile not in text:
    raise RuntimeError('mobile topbar CSS anchor not found')
text = text.replace(old_mobile, new_mobile, 1)

# Remove the drawer implementation entirely.
start = text.find('def render_drawer():\n')
end = text.find('\n\ndef topbar():\n', start)
if start == -1 or end == -1:
    raise RuntimeError('drawer function block not found')
text = text[:start] + text[end + 2:]

old_topbar = '''def topbar():\n    menu_col, brand_col, currency_col = st.columns([0.12, 1, 2.1], vertical_alignment="center")\n    with menu_col:\n        if st.button("☰", key="nav_toggle", help="開啟選單"):\n            st.session_state.menu_open = True\n            st.rerun()\n    with brand_col:\n        if st.button("MedSlime.", key=f"brand_home_{st.session_state.medslime_page}", help="返回首頁"):\n            goto("home")\n    with currency_col:\n        st.markdown(\n            f'<div class="currency"><span class="pill">🔥 {st.session_state.streak} 天</span><span class="pill">🪙 {st.session_state.coins}</span><span class="pill">🎫 {st.session_state.tickets}</span></div>',\n            unsafe_allow_html=True,\n        )\n'''
new_topbar = '''def topbar():\n    with st.container(key="topbar_shell"):\n        brand_col, currency_col = st.columns([1, 2.1], vertical_alignment="center")\n        with brand_col:\n            if st.button("MedSlime.", key=f"brand_home_{st.session_state.medslime_page}", help="返回首頁"):\n                goto("home")\n        with currency_col:\n            st.markdown(\n                f'<div class="currency"><span class="pill">🔥 {st.session_state.streak} 天</span><span class="pill">🪙 {st.session_state.coins}</span><span class="pill">🎫 {st.session_state.tickets}</span></div>',\n                unsafe_allow_html=True,\n            )\n'''
if old_topbar not in text:
    raise RuntimeError('topbar function anchor not found')
text = text.replace(old_topbar, new_topbar, 1)

# Add My Slime directly below Start Study on the home page.
old_home = '''        if st.button("🧠 開始學習", type="primary", use_container_width=True, key="home_start_study"):\n            goto("study")\n'''
new_home = '''        if st.button("🧠 開始學習", type="primary", use_container_width=True, key="home_start_study"):\n            goto("study")\n        if st.button("🐾 我的史萊姆", use_container_width=True, key="home_my_slime"):\n            goto("slime")\n'''
if old_home not in text:
    raise RuntimeError('home action anchor not found')
text = text.replace(old_home, new_home, 1)

# Make My Slime the hub for gacha and achievements.
old_slime_head = '''def slime_page():\n    topbar()\n    render_back_button("返回首頁", "home", "back_slime")\n    st.markdown("## 🐾 我的史萊姆")\n    left, right = st.columns([1, 1.35], gap="large")\n'''
new_slime_head = '''def slime_page():\n    topbar()\n    render_back_button("返回首頁", "home", "back_slime")\n    st.markdown("## 🐾 我的史萊姆")\n    gacha_col, achievement_col = st.columns(2)\n    with gacha_col:\n        if st.button("🎰 抽卡", use_container_width=True, key="slime_to_gacha"):\n            goto("gacha")\n    with achievement_col:\n        if st.button("🏆 成就", use_container_width=True, key="slime_to_achievements"):\n            goto("achievements")\n    left, right = st.columns([1, 1.35], gap="large")\n'''
if old_slime_head not in text:
    raise RuntimeError('slime page anchor not found')
text = text.replace(old_slime_head, new_slime_head, 1)

text = text.replace('render_back_button("返回首頁", "home", "back_achievements")', 'render_back_button("返回我的史萊姆", "slime", "back_achievements")', 1)
text = text.replace('render_back_button("返回首頁", "home", "back_gacha")', 'render_back_button("返回我的史萊姆", "slime", "back_gacha")', 1)

# Drawer should no longer be rendered at app startup.
if 'render_drawer()\n\npage = st.session_state.medslime_page' not in text:
    raise RuntimeError('render_drawer call not found')
text = text.replace('render_drawer()\n\npage = st.session_state.medslime_page', 'page = st.session_state.medslime_page', 1)

path.write_text(text, encoding='utf-8')
print('simplified MedSlime navigation')
