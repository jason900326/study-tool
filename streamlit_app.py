import random
import streamlit as st

st.set_page_config(
    page_title="MedSlime",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------
# Demo player state (MVP: later move to Supabase)
# ---------------------------------------------------------
DEFAULT_STATE = {
    "medslime_page": "home",
    "player_level": 4,
    "player_exp": 72,
    "coins": 420,
    "tickets": 2,
    "streak": 3,
    "slime_name": "Medi",
    "selected_slime": "青蘋果史萊姆",
    "collection": ["青蘋果史萊姆"],
    "unlocked_achievements": ["first_steps", "three_day_streak"],
    "last_gacha": None,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if isinstance(value, list) else value

ACHIEVEMENTS = [
    {"id": "first_steps", "icon": "🌱", "title": "第一步", "description": "完成第一次學習", "reward": "🪙 50"},
    {"id": "three_day_streak", "icon": "🔥", "title": "開始上癮", "description": "連續學習 3 天", "reward": "🎫 1"},
    {"id": "ten_correct", "icon": "🧠", "title": "腦袋熱身完畢", "description": "累積答對 10 題", "reward": "🪙 100"},
    {"id": "first_review", "icon": "🔍", "title": "抓到弱點", "description": "完成第一次錯題訂正", "reward": "🪙 80"},
    {"id": "level_five", "icon": "⭐", "title": "史萊姆長大了", "description": "史萊姆升到 Lv.5", "reward": "🎫 1"},
    {"id": "study_30", "icon": "⏱️", "title": "專注半小時", "description": "累積專注學習 30 分鐘", "reward": "🪙 120"},
]

GACHA_POOL = [
    {"name": "青蘋果史萊姆", "rarity": "N", "emoji": "🟢", "weight": 35},
    {"name": "薄荷史萊姆", "rarity": "N", "emoji": "🟩", "weight": 35},
    {"name": "藍莓史萊姆", "rarity": "R", "emoji": "🔵", "weight": 14},
    {"name": "葡萄史萊姆", "rarity": "R", "emoji": "🟣", "weight": 11},
    {"name": "黃金史萊姆", "rarity": "SSR", "emoji": "🟡", "weight": 4},
    {"name": "星空史萊姆", "rarity": "SSR", "emoji": "🌌", "weight": 1},
]

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 10% 5%, rgba(132, 255, 179, .20), transparent 26%),
            radial-gradient(circle at 90% 18%, rgba(115, 222, 255, .16), transparent 25%),
            #f7fbf8;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: #f7fbf8; }
    .block-container { max-width: 1180px; padding-top: 1.2rem; padding-bottom: 5rem; }
    h1, h2, h3, p, div, button { font-family: "Noto Sans TC", "Microsoft JhengHei", sans-serif; }
    .topbar { display:flex; align-items:center; justify-content:space-between; margin-bottom: 1.15rem; }
    .brand { font-size:1.55rem; font-weight:900; letter-spacing:-.04em; color:#17372a; }
    .brand-dot { color:#31b96c; }
    .currency { display:inline-flex; gap:.55rem; flex-wrap:wrap; justify-content:flex-end; }
    .pill { background:rgba(255,255,255,.86); border:1px solid #dcebe2; border-radius:999px; padding:.42rem .72rem; font-weight:800; color:#244c39; box-shadow:0 5px 18px rgba(37,92,62,.06); }
    .hero { background:linear-gradient(135deg,#dff8e8 0%,#effcf3 55%,#e8f9ff 100%); border:1px solid #d2eadb; border-radius:30px; padding:2rem; box-shadow:0 18px 45px rgba(40,106,69,.10); margin-bottom:1.25rem; overflow:hidden; }
    .eyebrow { color:#31955e; font-weight:900; font-size:.9rem; margin-bottom:.35rem; }
    .hero-title { font-size:2.25rem; line-height:1.15; font-weight:950; color:#143629; letter-spacing:-.05em; }
    .hero-copy { color:#557265; margin-top:.55rem; max-width:610px; line-height:1.7; }
    .slime-stage { text-align:center; padding:1rem 0 .25rem; }
    .slime { width:178px; height:142px; margin:0 auto 1rem; border-radius:50% 50% 40% 40% / 62% 62% 38% 38%; background:linear-gradient(145deg,#9bedad,#48c878); box-shadow:inset -14px -18px 0 rgba(25,130,74,.09), 0 20px 30px rgba(39,139,82,.18); position:relative; }
    .slime:before,.slime:after { content:""; position:absolute; top:60px; width:13px; height:19px; background:#153c2b; border-radius:50%; }
    .slime:before { left:49px; } .slime:after { right:49px; }
    .mouth { position:absolute; width:35px; height:15px; border-bottom:4px solid #153c2b; border-radius:0 0 50% 50%; left:72px; top:88px; }
    .shine { position:absolute; width:32px; height:16px; background:rgba(255,255,255,.48); border-radius:50%; left:35px; top:29px; transform:rotate(-24deg); }
    .lvl { font-size:1.02rem; font-weight:900; color:#1f4c37; }
    .xp-track { height:10px; background:#dbe9df; border-radius:999px; overflow:hidden; margin:.45rem auto .2rem; max-width:310px; }
    .xp-fill { height:100%; border-radius:999px; background:linear-gradient(90deg,#50cb7e,#42b9a3); }
    .card { background:rgba(255,255,255,.9); border:1px solid #e0ece4; border-radius:22px; padding:1.1rem 1.2rem; box-shadow:0 8px 24px rgba(31,83,53,.06); height:100%; }
    .card-title { color:#1d4533; font-weight:900; font-size:1.08rem; }
    .muted { color:#71887b; font-size:.92rem; }
    .section-title { font-size:1.35rem; font-weight:950; color:#173b2b; margin:1.55rem 0 .8rem; }
    .achievement { border-radius:20px; padding:1rem; border:1px solid #deebe3; background:#fff; min-height:155px; }
    .achievement.locked { filter:grayscale(.75); opacity:.62; }
    .achievement-icon { font-size:2rem; }
    .achievement-title { font-weight:900; color:#214632; margin-top:.45rem; }
    .rarity-N { color:#6b7d72; font-weight:900; }
    .rarity-R { color:#3d72c8; font-weight:900; }
    .rarity-SSR { color:#b58213; font-weight:950; }
    .gacha-result { text-align:center; background:white; border:1px solid #dcebe2; border-radius:28px; padding:2rem; box-shadow:0 14px 35px rgba(32,89,57,.09); }
    .gacha-emoji { font-size:5rem; line-height:1.2; }
    .tiny-label { color:#789083; font-size:.82rem; font-weight:800; letter-spacing:.05em; text-transform:uppercase; }
    div.stButton > button { border-radius:15px; min-height:46px; font-weight:850; border:1px solid #d6e9dc; }
    div.stButton > button[kind="primary"] { background:#2fb96c; color:white; border-color:#2fb96c; }
    </style>
    """,
    unsafe_allow_html=True,
)


def goto(page):
    st.session_state.medslime_page = page
    st.rerun()


def topbar():
    st.markdown(f"""
        <div class="topbar">
            <div class="brand">MedSlime<span class="brand-dot">.</span></div>
            <div class="currency">
                <span class="pill">🔥 {st.session_state.streak} 天</span>
                <span class="pill">🪙 {st.session_state.coins}</span>
                <span class="pill">🎫 {st.session_state.tickets}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def nav_row(active):
    items = [("home", "🏠 首頁"), ("slime", "🐾 史萊姆"), ("gacha", "🎰 抽卡"), ("achievements", "🏆 成就")]
    cols = st.columns(4)
    for col, (page, label) in zip(cols, items):
        with col:
            if st.button(label, key=f"nav_{page}", use_container_width=True, type="primary" if page == active else "secondary"):
                goto(page)


def show_slime():
    st.markdown(f"""
        <div class="slime-stage">
            <div class="slime"><div class="shine"></div><div class="mouth"></div></div>
            <div class="lvl">{st.session_state.slime_name} · Lv.{st.session_state.player_level}</div>
            <div class="xp-track"><div class="xp-fill" style="width:{st.session_state.player_exp}%"></div></div>
            <div class="muted">{st.session_state.player_exp} / 100 EXP · {st.session_state.selected_slime}</div>
        </div>
        """, unsafe_allow_html=True)


def page_home():
    topbar()
    left, right = st.columns([1.45, 1], gap="large")
    with left:
        st.markdown("""
            <div class="hero">
                <div class="eyebrow">TODAY'S STUDY</div>
                <div class="hero-title">把今天的知識<br>餵給你的史萊姆。</div>
                <div class="hero-copy">做題、訂正與專注學習都會讓史萊姆成長。先完成一小段，再去看看今天能不能拿到新的抽卡券。</div>
            </div>
            """, unsafe_allow_html=True)
        c1, c2 = st.columns([1.4, 1])
        with c1:
            if st.button("🧠 開始學習", type="primary", use_container_width=True):
                st.switch_page("pages/學習.py")
        with c2:
            if st.button("🔍 看我的弱點", use_container_width=True):
                st.switch_page("pages/學習.py")
    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        show_slime()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">今日任務</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    tasks = [("🧠", "完成 5 題", "0 / 5", "+20 EXP"), ("🔍", "訂正 1 題", "0 / 1", "+50 🪙"), ("⏱️", "學習 20 分鐘", "0 / 20", "+1 🎫")]
    for col, (icon, title, progress, reward) in zip(cols, tasks):
        with col:
            st.markdown(f'<div class="card"><div style="font-size:1.7rem">{icon}</div><div class="card-title">{title}</div><div class="muted">{progress}</div><div style="margin-top:.7rem;font-weight:900;color:#2a9d5e">{reward}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">探索 MedSlime</div>', unsafe_allow_html=True)
    nav_row("home")


def page_slime():
    topbar()
    st.markdown("## 🐾 我的史萊姆")
    left, right = st.columns([1, 1.35], gap="large")
    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        show_slime()
        new_name = st.text_input("史萊姆名字", value=st.session_state.slime_name, max_chars=16)
        if new_name != st.session_state.slime_name:
            st.session_state.slime_name = new_name
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown('<div class="card-title">收藏</div><div class="muted">抽到的史萊姆會出現在這裡。</div><br>', unsafe_allow_html=True)
        for slime in st.session_state.collection:
            chosen = slime == st.session_state.selected_slime
            if st.button(("✅ " if chosen else "🟢 ") + slime, key=f"slime_{slime}", use_container_width=True):
                st.session_state.selected_slime = slime
                st.rerun()
        st.info("MVP 先做收藏與切換。進化、裝飾品與技能之後再接。")
    st.markdown('<div class="section-title">導覽</div>', unsafe_allow_html=True)
    nav_row("slime")


def page_achievements():
    topbar()
    unlocked = set(st.session_state.unlocked_achievements)
    st.markdown("## 🏆 成就")
    st.caption(f"目前解鎖 {len(unlocked)} / {len(ACHIEVEMENTS)}")
    cols = st.columns(3)
    for i, item in enumerate(ACHIEVEMENTS):
        done = item["id"] in unlocked
        klass = "achievement" if done else "achievement locked"
        status = "已解鎖" if done else "尚未解鎖"
        with cols[i % 3]:
            st.markdown(f'<div class="{klass}"><div class="achievement-icon">{item["icon"]}</div><div class="achievement-title">{item["title"]}</div><div class="muted">{item["description"]}</div><div style="margin-top:.65rem;font-weight:850">{status} · {item["reward"]}</div></div><br>', unsafe_allow_html=True)
    nav_row("achievements")


def pull_gacha():
    if st.session_state.tickets <= 0:
        return None
    st.session_state.tickets -= 1
    result = random.choices(GACHA_POOL, weights=[x["weight"] for x in GACHA_POOL], k=1)[0]
    duplicate = result["name"] in st.session_state.collection
    if duplicate:
        st.session_state.coins += 50 if result["rarity"] == "N" else 120 if result["rarity"] == "R" else 300
    else:
        st.session_state.collection.append(result["name"])
    st.session_state.last_gacha = {**result, "duplicate": duplicate}
    return result


def page_gacha():
    topbar()
    st.markdown("## 🎰 史萊姆召喚")
    st.caption("學習拿票券，票券用來召喚新的史萊姆。第一版先把獎勵循環跑起來。")
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.markdown("""
            <div class="card"><div class="tiny-label">SLIME CAPSULE</div><div style="font-size:4.4rem;text-align:center;padding:.8rem">🧪</div><div class="card-title" style="text-align:center">1 張票券 = 1 次召喚</div><div class="muted" style="text-align:center;margin-top:.35rem">N 70% · R 25% · SSR 5%</div></div>
            """, unsafe_allow_html=True)
        if st.button("🎫 召喚一次", type="primary", use_container_width=True, disabled=st.session_state.tickets <= 0):
            pull_gacha()
            st.rerun()
        if st.session_state.tickets <= 0:
            st.warning("目前沒有抽卡券。之後會由學習任務與成就取得。")
    with right:
        result = st.session_state.last_gacha
        if result:
            duplicate_text = "重複獲得，已轉換成金幣" if result["duplicate"] else "NEW！已加入收藏"
            st.markdown(f'<div class="gacha-result"><div class="tiny-label">{duplicate_text}</div><div class="gacha-emoji">{result["emoji"]}</div><div class="rarity-{result["rarity"]}">{result["rarity"]}</div><div style="font-size:1.35rem;font-weight:950;color:#1e4934">{result["name"]}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="gacha-result"><div class="gacha-emoji">❔</div><div class="muted">你的下一隻史萊姆會是誰？</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">目前卡池</div>', unsafe_allow_html=True)
    pool_cols = st.columns(3)
    for i, item in enumerate(GACHA_POOL):
        with pool_cols[i % 3]:
            st.markdown(f'<div class="card"><div style="font-size:2rem">{item["emoji"]}</div><div class="card-title">{item["name"]}</div><div class="rarity-{item["rarity"]}">{item["rarity"]}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">導覽</div>', unsafe_allow_html=True)
    nav_row("gacha")


page = st.session_state.medslime_page
if page == "home":
    page_home()
elif page == "slime":
    page_slime()
elif page == "achievements":
    page_achievements()
elif page == "gacha":
    page_gacha()
else:
    st.session_state.medslime_page = "home"
    st.rerun()
