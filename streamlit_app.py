import random
import streamlit as st

st.set_page_config(
    page_title="MedSlime",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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
    "uploaded_learning_file": None,
}

for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if isinstance(value, list) else value

ACHIEVEMENTS = [
    ("first_steps", "🌱", "第一步", "完成第一次學習", "🪙 50"),
    ("three_day_streak", "🔥", "開始上癮", "連續學習 3 天", "🎫 1"),
    ("ten_correct", "🧠", "腦袋熱身完畢", "累積答對 10 題", "🪙 100"),
    ("first_review", "🔍", "抓到弱點", "完成第一次錯題訂正", "🪙 80"),
    ("level_five", "⭐", "史萊姆長大了", "史萊姆升到 Lv.5", "🎫 1"),
    ("study_30", "⏱️", "專注半小時", "累積專注學習 30 分鐘", "🪙 120"),
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
    :root { --ink:#153b2b; --green:#31c978; --line:#dbe9e1; }
    .stApp {
        background:
            radial-gradient(circle at 8% 3%, rgba(130,239,173,.18), transparent 24%),
            radial-gradient(circle at 93% 13%, rgba(118,220,255,.15), transparent 23%),
            #f8fcf9;
    }
    [data-testid="stHeader"] { background:transparent; }
    .block-container { max-width:1180px; padding-top:1rem; padding-bottom:4.5rem; }
    h1,h2,h3,p,div,button,label { font-family:"Noto Sans TC","Microsoft JhengHei",sans-serif; }

    .currency { display:flex; gap:.55rem; justify-content:flex-end; align-items:center; flex-wrap:wrap; }
    .pill { background:rgba(255,255,255,.9); border:1px solid #dfece4; border-radius:999px; padding:.5rem .8rem; font-weight:850; color:#244c39; box-shadow:0 6px 18px rgba(31,83,53,.045); }
    .eyebrow { color:#2ba962; font-weight:950; font-size:.86rem; letter-spacing:.04em; text-transform:uppercase; }
    .hero-title { font-size:2.25rem; line-height:1.12; font-weight:950; color:#143629; letter-spacing:-.045em; }
    .hero-copy { color:#637f70; margin-top:.6rem; line-height:1.72; }
    .section-title { font-size:1.34rem; font-weight:950; color:#173b2b; margin:1.7rem 0 .85rem; }
    .muted { color:#71887b; font-size:.92rem; }
    .card-title { color:#1d4533; font-weight:900; font-size:1.08rem; }

    /* Clickable brand that still looks exactly like a logo */
    [class*="st-key-brand_home_"] button {
        background:transparent !important;
        border:none !important;
        box-shadow:none !important;
        padding:0 !important;
        min-height:auto !important;
        color:#17372a !important;
        font-size:1.55rem !important;
        font-weight:950 !important;
        letter-spacing:-.035em !important;
    }
    [class*="st-key-brand_home_"] button:hover {
        background:transparent !important;
        border:none !important;
        transform:none !important;
        color:#17372a !important;
    }
    [class*="st-key-brand_home_"] button p { font-size:1.55rem !important; font-weight:950 !important; }

    /* New home */
    .home-hero {
        position:relative; overflow:hidden;
        background:linear-gradient(135deg,#e6f9ed 0%,#f5fcf7 57%,#e9f8fd 100%);
        border:1px solid #d6eadd; border-radius:32px; padding:2rem 2rem 1.8rem;
        box-shadow:0 18px 44px rgba(40,106,69,.09);
        min-height:300px;
    }
    .home-hero:after {
        content:""; position:absolute; width:230px; height:230px; right:-80px; bottom:-110px;
        border-radius:50%; background:rgba(66,201,125,.08);
    }
    .home-copy-wrap { padding:.15rem .2rem 0; }
    .home-slime-wrap { display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:250px; }
    .home-slime-label { font-weight:950; color:#214934; margin-top:.1rem; }
    .home-xp { width:82%; max-width:300px; height:9px; border-radius:999px; overflow:hidden; background:#dce9df; margin:.55rem auto .25rem; }
    .home-xp-fill { height:100%; background:linear-gradient(90deg,#58d28a,#42bda4); }
    .home-task { background:rgba(255,255,255,.95); border:1px solid #dfebe4; border-radius:23px; padding:1.2rem 1.25rem; box-shadow:0 10px 26px rgba(31,83,53,.05); min-height:145px; }
    .task-icon { width:44px; height:44px; border-radius:14px; display:flex; align-items:center; justify-content:center; background:#eefaf2; font-size:1.45rem; margin-bottom:.7rem; }
    .task-reward { margin-top:.7rem; font-weight:900; color:#2a9d5e; }

    .choice-card { background:rgba(255,255,255,.96); border:1px solid #dceae2; border-radius:25px; padding:1.45rem 1.5rem; min-height:156px; box-shadow:0 12px 28px rgba(30,78,50,.055); }
    .choice-icon-shell { width:50px; height:50px; border-radius:15px; display:flex; align-items:center; justify-content:center; background:linear-gradient(145deg,#e8f9ee,#f1fbf5); border:1px solid #d7eadf; margin-bottom:.9rem; }
    .choice-icon { font-size:1.72rem; }
    .choice-title { font-size:1.17rem; font-weight:950; color:#173b2b; }
    .choice-copy { color:#70877a; line-height:1.55; margin-top:.42rem; }
    .study-header { margin:.35rem 0 1.2rem; }

    .intro-panel { max-width:840px; margin:.3rem auto 1.15rem; background:rgba(255,255,255,.76); border:1px solid #dfebe4; border-radius:30px; padding:2rem 2rem 1.75rem; box-shadow:0 16px 38px rgba(30,82,51,.055); text-align:center; }
    .intro-art { position:relative; width:230px; height:150px; margin:0 auto .65rem; }
    .mini-slime { position:absolute; left:42px; top:35px; width:105px; height:82px; border-radius:50% 50% 40% 40%/62% 62% 38% 38%; background:linear-gradient(145deg,#9bedad,#48c878); box-shadow:inset -9px -10px 0 rgba(25,130,74,.08),0 14px 24px rgba(39,139,82,.14); }
    .mini-slime:before,.mini-slime:after { content:""; position:absolute; top:34px; width:8px; height:12px; background:#153c2b; border-radius:50%; }
    .mini-slime:before { left:30px; } .mini-slime:after { right:30px; }
    .mini-mouth { position:absolute; width:23px; height:9px; border-bottom:3px solid #153c2b; border-radius:0 0 50% 50%; left:41px; top:50px; }
    .mini-shine { position:absolute; width:22px; height:10px; background:rgba(255,255,255,.52); border-radius:50%; left:20px; top:16px; transform:rotate(-23deg); }
    .book-stack { position:absolute; right:34px; top:34px; font-size:3.6rem; }
    .check-list { max-width:575px; margin:1rem auto .2rem; text-align:left; display:grid; gap:.55rem; }
    .check-item { color:#315b47; font-weight:760; background:#f7fcf9; border:1px solid #e0eee6; border-radius:13px; padding:.62rem .8rem; }

    .upload-shell { background:rgba(255,255,255,.92); border:1px solid #dceae2; border-radius:27px; padding:1.1rem 1.15rem 1.2rem; box-shadow:0 12px 30px rgba(30,78,50,.05); }
    [data-testid="stFileUploaderDropzone"] { background:#fbfefc !important; border:1.5px dashed #bcdcc8 !important; border-radius:20px !important; padding:1.6rem !important; }
    [data-testid="stFileUploaderDropzone"] button { background:#2fc675 !important; color:white !important; border-color:#2fc675 !important; }

    .slime { width:178px; height:142px; margin:0 auto 1rem; border-radius:50% 50% 40% 40%/62% 62% 38% 38%; background:linear-gradient(145deg,#9bedad,#48c878); box-shadow:inset -14px -18px 0 rgba(25,130,74,.09),0 20px 30px rgba(39,139,82,.18); position:relative; }
    .slime:before,.slime:after { content:""; position:absolute; top:60px; width:13px; height:19px; background:#153c2b; border-radius:50%; }
    .slime:before { left:49px; } .slime:after { right:49px; }
    .mouth { position:absolute; width:35px; height:15px; border-bottom:4px solid #153c2b; border-radius:0 0 50% 50%; left:72px; top:88px; }
    .shine { position:absolute; width:32px; height:16px; background:rgba(255,255,255,.48); border-radius:50%; left:35px; top:29px; transform:rotate(-24deg); }
    .locked { filter:grayscale(.8); opacity:.55; }
    .gacha-result { text-align:center; background:white; border:1px solid #dcebe2; border-radius:28px; padding:2rem; }
    .rarity-N { color:#6b7d72; font-weight:900; }.rarity-R { color:#3d72c8; font-weight:900; }.rarity-SSR { color:#b58213; font-weight:950; }

    div.stButton > button { border-radius:15px; min-height:46px; font-weight:850; transition:.15s ease; }
    div.stButton > button:hover { transform:translateY(-1px); }
    div.stButton > button[kind="primary"] { background:#31c978; color:white; border:1px solid #31c978; box-shadow:0 7px 18px rgba(49,201,120,.16); }
    div.stButton > button[kind="secondary"] { background:rgba(255,255,255,.9); color:#244c39; border:1px solid #d8e8df; }
    div.stButton > button:disabled { background:#f2f6f3 !important; color:#9aac9f !important; border-color:#e2ebe5 !important; }

    @media (max-width:700px) {
        .block-container { padding-left:1rem; padding-right:1rem; }
        .hero-title { font-size:1.9rem; }
        .home-hero { padding:1.35rem; }
        .choice-card { min-height:145px; padding:1.2rem; }
        .intro-panel { padding:1.45rem 1.1rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def goto(page):
    st.session_state.medslime_page = page
    st.rerun()


def topbar():
    brand_col, currency_col = st.columns([1, 2.15], vertical_alignment="center")
    with brand_col:
        if st.button("MedSlime.", key=f"brand_home_{st.session_state.medslime_page}"):
            goto("home")
    with currency_col:
        st.markdown(
            f'<div class="currency"><span class="pill">🔥 {st.session_state.streak} 天</span><span class="pill">🪙 {st.session_state.coins}</span><span class="pill">🎫 {st.session_state.tickets}</span></div>',
            unsafe_allow_html=True,
        )


def nav(active):
    items = [
        ("home", "🏠 首頁"),
        ("study", "📖 學習"),
        ("slime", "🐾 史萊姆"),
        ("gacha", "🎰 抽卡"),
        ("achievements", "🏆 成就"),
    ]
    cols = st.columns(5)
    for col, (page, label) in zip(cols, items):
        with col:
            if st.button(label, key=f"nav_{page}", use_container_width=True, type="primary" if page == active else "secondary"):
                goto(page)


def slime_markup():
    return '<div class="slime"><div class="shine"></div><div class="mouth"></div></div>'


def home():
    topbar()
    st.markdown('<div class="home-hero">', unsafe_allow_html=True)
    left, right = st.columns([1.35, 1], gap="large", vertical_alignment="center")
    with left:
        st.markdown(
            '<div class="home-copy-wrap">'
            '<div class="eyebrow">TODAY\'S STUDY</div>'
            '<div class="hero-title">把今天的知識<br>餵給你的史萊姆。</div>'
            '<div class="hero-copy">做題、訂正與專注學習都會讓史萊姆成長。先完成一小段，再去看看今天能不能拿到新的抽卡券。</div>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button("🧠 開始學習", type="primary", use_container_width=True, key="home_start_study"):
            goto("study")
    with right:
        st.markdown(
            '<div class="home-slime-wrap">'
            + slime_markup()
            + f'<div class="home-slime-label">{st.session_state.slime_name} · Lv.{st.session_state.player_level}</div>'
            + f'<div class="home-xp"><div class="home-xp-fill" style="width:{st.session_state.player_exp}%"></div></div>'
            + f'<div class="muted">{st.session_state.player_exp} / 100 EXP · {st.session_state.selected_slime}</div>'
            + '</div>',
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">今日任務</div>', unsafe_allow_html=True)
    tasks = [
        ("🧠", "完成 5 題", "0 / 5", "+20 EXP"),
        ("🔍", "訂正 1 題", "0 / 1", "+50 🪙"),
        ("⏱️", "學習 20 分鐘", "0 / 20", "+1 🎫"),
    ]
    cols = st.columns(3, gap="medium")
    for col, (icon, title, progress, reward) in zip(cols, tasks):
        with col:
            st.markdown(
                f'<div class="home-task"><div class="task-icon">{icon}</div><div class="card-title">{title}</div><div class="muted">{progress}</div><div class="task-reward">{reward}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section-title">探索 MedSlime</div>', unsafe_allow_html=True)
    nav("home")


def study_home():
    topbar()
    st.markdown('<div class="study-header"><div class="eyebrow">STUDY</div><div class="hero-title" style="font-size:2.05rem">你想怎麼學習呢？</div><div class="hero-copy">選擇適合你現在狀態的方式，MedSlime 陪你一起進步。</div></div>', unsafe_allow_html=True)

    rows = [
        [("📄", "我有教材", "上傳 PDF 教材，讓 AI 幫你整理重點並生成測驗。", "study_material_intro"), ("🧪", "我要刷國考", "練習歷屆國考題目，快速檢測實力與弱點。", None)],
        [("📘", "我要複習錯題", "回顧答錯或不確定的題目，加強你的弱點。", None), ("⏱️", "我要專心讀書", "進入專注計時器，累積今天的學習效率。", None)],
    ]
    for row in rows:
        cols = st.columns(2, gap="large")
        for col, (icon, title, copy, target) in zip(cols, row):
            with col:
                st.markdown(f'<div class="choice-card"><div class="choice-icon-shell"><div class="choice-icon">{icon}</div></div><div class="choice-title">{title}</div><div class="choice-copy">{copy}</div></div>', unsafe_allow_html=True)
                if target:
                    if st.button(f"進入 {title} →", key=f"go_{target}", use_container_width=True, type="primary"):
                        goto(target)
                else:
                    st.button("即將開放", key=f"soon_{title}", use_container_width=True, disabled=True)
        st.write("")
    nav("study")


def study_material_intro():
    topbar()
    if st.button("← 返回學習", key="intro_back"):
        goto("study")

    st.markdown(
        '<div class="intro-panel">'
        '<div class="intro-art"><div class="mini-slime"><div class="mini-shine"></div><div class="mini-mouth"></div></div><div class="book-stack">📚</div></div>'
        '<div class="hero-title" style="font-size:2rem">上傳教材，AI 幫你整理重點<br>並生成專屬測驗。</div>'
        '<div class="hero-copy" style="max-width:680px;margin:.8rem auto 0">先不用把整份教材硬啃完。MedSlime 會先抓重點，再用題目幫你找出真正需要花時間的地方。</div>'
        '<div class="check-list">'
        '<div class="check-item">✓ 快速擷取教材重點</div>'
        '<div class="check-item">✓ 生成適合複習的選擇題</div>'
        '<div class="check-item">✓ 標記不確定與答錯觀念</div>'
        '<div class="check-item">✓ 把需要加強的內容留下來</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )
    if st.button("☁️ 上傳教材開始學習", type="primary", use_container_width=True):
        goto("study_material_upload")
    nav("study")


def study_material_upload():
    topbar()
    if st.button("← 返回介紹", key="upload_back"):
        goto("study_material_intro")

    st.markdown('<div class="study-header"><div class="eyebrow">YOUR MATERIAL</div><div class="hero-title" style="font-size:2.05rem">上傳你的教材</div><div class="hero-copy">目前先支援 PDF。建議使用含有可選取文字的檔案。</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="upload-shell">', unsafe_allow_html=True)
    uploaded = st.file_uploader("選擇 PDF 教材", type=["pdf"], key="medslime_material_pdf")
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded is not None:
        st.session_state.uploaded_learning_file = uploaded.name
        size_mb = len(uploaded.getvalue()) / (1024 * 1024)
        st.success(f"已選擇：{uploaded.name} · {size_mb:.1f} MB")
        st.info("目前先完成新的 MedSlime 上傳流程；AI 分析會在下一步接回原本穩定的教材處理邏輯。")
        st.button("✨ 開始 AI 分析", type="primary", use_container_width=True, disabled=True)
    else:
        st.caption("小提醒：掃描型 PDF 或大量圖片頁面，之後需要另外處理圖片辨識。")
    nav("study")


def slime_page():
    topbar()
    st.markdown("## 🐾 我的史萊姆")
    left, right = st.columns([1, 1.35], gap="large")
    with left:
        st.markdown('<div style="text-align:center;padding:1.2rem;background:white;border:1px solid #dfebe4;border-radius:24px">' + slime_markup() + '</div>', unsafe_allow_html=True)
        st.session_state.slime_name = st.text_input("史萊姆名字", value=st.session_state.slime_name, max_chars=16)
    with right:
        st.markdown("### 收藏")
        for slime in st.session_state.collection:
            if st.button(("✅ " if slime == st.session_state.selected_slime else "🟢 ") + slime, key=f"slime_{slime}", use_container_width=True):
                st.session_state.selected_slime = slime
                st.rerun()
    nav("slime")


def achievements_page():
    topbar()
    st.markdown("## 🏆 成就")
    unlocked = set(st.session_state.unlocked_achievements)
    st.caption(f"目前解鎖 {len(unlocked)} / {len(ACHIEVEMENTS)}")
    cols = st.columns(3)
    for i, (aid, icon, title, desc, reward) in enumerate(ACHIEVEMENTS):
        style = "opacity:1" if aid in unlocked else "filter:grayscale(.8);opacity:.55"
        status = "已解鎖" if aid in unlocked else "尚未解鎖"
        with cols[i % 3]:
            st.markdown(f'<div style="{style};background:white;border:1px solid #dfebe4;border-radius:22px;padding:1rem;min-height:150px"><div style="font-size:2rem">{icon}</div><div class="card-title">{title}</div><div class="muted">{desc}</div><div style="margin-top:.6rem;font-weight:850">{status} · {reward}</div></div><br>', unsafe_allow_html=True)
    nav("achievements")


def gacha_page():
    topbar()
    st.markdown("## 🎰 史萊姆召喚")
    st.caption("1 張抽卡券 = 1 次召喚 · N 70% · R 25% · SSR 5%")
    if st.button("🎫 召喚一次", type="primary", use_container_width=True, disabled=st.session_state.tickets <= 0):
        st.session_state.tickets -= 1
        result = random.choices(GACHA_POOL, weights=[x["weight"] for x in GACHA_POOL], k=1)[0]
        duplicate = result["name"] in st.session_state.collection
        if duplicate:
            st.session_state.coins += 50 if result["rarity"] == "N" else 120 if result["rarity"] == "R" else 300
        else:
            st.session_state.collection.append(result["name"])
        st.session_state.last_gacha = {**result, "duplicate": duplicate}
        st.rerun()
    result = st.session_state.last_gacha
    if result:
        msg = "重複獲得，已轉換成金幣" if result["duplicate"] else "NEW！已加入收藏"
        st.markdown(f'<div class="gacha-result"><div class="muted">{msg}</div><div style="font-size:5rem">{result["emoji"]}</div><div class="rarity-{result["rarity"]}">{result["rarity"]}</div><div class="card-title">{result["name"]}</div></div>', unsafe_allow_html=True)
    nav("gacha")


page = st.session_state.medslime_page
if page == "home":
    home()
elif page == "study":
    study_home()
elif page == "study_material_intro":
    study_material_intro()
elif page == "study_material_upload":
    study_material_upload()
elif page == "slime":
    slime_page()
elif page == "gacha":
    gacha_page()
elif page == "achievements":
    achievements_page()
else:
    st.session_state.medslime_page = "home"
    st.rerun()
