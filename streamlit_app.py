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
    .stApp {background:radial-gradient(circle at 10% 5%,rgba(132,255,179,.20),transparent 26%),radial-gradient(circle at 90% 18%,rgba(115,222,255,.16),transparent 25%),#f7fbf8;}
    [data-testid="stHeader"]{background:transparent}.block-container{max-width:1180px;padding-top:1.2rem;padding-bottom:5rem}
    h1,h2,h3,p,div,button{font-family:"Noto Sans TC","Microsoft JhengHei",sans-serif}
    .topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.15rem}.brand{font-size:1.55rem;font-weight:900;color:#17372a}.dot{color:#31b96c}
    .currency{display:inline-flex;gap:.55rem;flex-wrap:wrap}.pill{background:rgba(255,255,255,.86);border:1px solid #dcebe2;border-radius:999px;padding:.42rem .72rem;font-weight:800;color:#244c39}
    .hero{background:linear-gradient(135deg,#dff8e8,#effcf3 55%,#e8f9ff);border:1px solid #d2eadb;border-radius:30px;padding:2rem;box-shadow:0 18px 45px rgba(40,106,69,.10);margin-bottom:1.25rem}
    .eyebrow{color:#31955e;font-weight:900;font-size:.9rem}.hero-title{font-size:2.25rem;line-height:1.15;font-weight:950;color:#143629;letter-spacing:-.05em}.hero-copy{color:#557265;margin-top:.55rem;line-height:1.7}
    .card{background:rgba(255,255,255,.92);border:1px solid #e0ece4;border-radius:22px;padding:1.2rem 1.25rem;box-shadow:0 8px 24px rgba(31,83,53,.06);height:100%}.card-title{color:#1d4533;font-weight:900;font-size:1.08rem}.muted{color:#71887b;font-size:.92rem}.section-title{font-size:1.35rem;font-weight:950;color:#173b2b;margin:1.55rem 0 .8rem}
    .choice-card{background:#fff;border:1px solid #dfece4;border-radius:24px;padding:1.3rem;min-height:170px;box-shadow:0 10px 24px rgba(31,83,53,.055)}.choice-icon{font-size:2.15rem;margin-bottom:.55rem}.choice-title{font-size:1.15rem;font-weight:950;color:#173b2b}.choice-copy{color:#71887b;line-height:1.55;margin-top:.35rem}
    .intro-wrap{text-align:center;padding:1rem 0}.intro-slime{font-size:5rem}.check-list{max-width:560px;margin:1rem auto;text-align:left}.check-item{margin:.55rem 0;color:#315b47;font-weight:700}
    .upload-box{background:rgba(255,255,255,.92);border:1px solid #dfece4;border-radius:24px;padding:1.4rem;box-shadow:0 10px 24px rgba(31,83,53,.055)}
    .slime-stage{text-align:center;padding:1rem 0 .25rem}.slime{width:178px;height:142px;margin:0 auto 1rem;border-radius:50% 50% 40% 40%/62% 62% 38% 38%;background:linear-gradient(145deg,#9bedad,#48c878);box-shadow:inset -14px -18px 0 rgba(25,130,74,.09),0 20px 30px rgba(39,139,82,.18);position:relative}.slime:before,.slime:after{content:"";position:absolute;top:60px;width:13px;height:19px;background:#153c2b;border-radius:50%}.slime:before{left:49px}.slime:after{right:49px}.mouth{position:absolute;width:35px;height:15px;border-bottom:4px solid #153c2b;border-radius:0 0 50% 50%;left:72px;top:88px}.shine{position:absolute;width:32px;height:16px;background:rgba(255,255,255,.48);border-radius:50%;left:35px;top:29px;transform:rotate(-24deg)}
    .xp-track{height:10px;background:#dbe9df;border-radius:999px;overflow:hidden;margin:.45rem auto .2rem;max-width:310px}.xp-fill{height:100%;background:linear-gradient(90deg,#50cb7e,#42b9a3)}
    .locked{filter:grayscale(.8);opacity:.55}.gacha-result{text-align:center;background:white;border:1px solid #dcebe2;border-radius:28px;padding:2rem}.rarity-N{color:#6b7d72;font-weight:900}.rarity-R{color:#3d72c8;font-weight:900}.rarity-SSR{color:#b58213;font-weight:950}
    div.stButton>button{border-radius:15px;min-height:46px;font-weight:850;border:1px solid #d6e9dc}div.stButton>button[kind="primary"]{background:#2fb96c;color:white;border-color:#2fb96c}
    </style>
    """,
    unsafe_allow_html=True,
)


def goto(page):
    st.session_state.medslime_page = page
    st.rerun()


def topbar():
    st.markdown(
        f'<div class="topbar"><div class="brand">MedSlime<span class="dot">.</span></div><div class="currency"><span class="pill">🔥 {st.session_state.streak} 天</span><span class="pill">🪙 {st.session_state.coins}</span><span class="pill">🎫 {st.session_state.tickets}</span></div></div>',
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


def slime_card():
    st.markdown(
        f'<div class="slime-stage"><div class="slime"><div class="shine"></div><div class="mouth"></div></div><div style="font-weight:900">{st.session_state.slime_name} · Lv.{st.session_state.player_level}</div><div class="xp-track"><div class="xp-fill" style="width:{st.session_state.player_exp}%"></div></div><div class="muted">{st.session_state.player_exp} / 100 EXP · {st.session_state.selected_slime}</div></div>',
        unsafe_allow_html=True,
    )


def home():
    topbar()
    left, right = st.columns([1.45, 1], gap="large")
    with left:
        st.markdown('<div class="hero"><div class="eyebrow">TODAY\'S STUDY</div><div class="hero-title">把今天的知識<br>餵給你的史萊姆。</div><div class="hero-copy">做題、訂正與專注學習都會讓史萊姆成長。完成一小段，再去看看今天能不能拿到新的抽卡券。</div></div>', unsafe_allow_html=True)
        if st.button("🧠 開始學習", type="primary", use_container_width=True):
            goto("study")
    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        slime_card()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-title">今日任務</div>', unsafe_allow_html=True)
    tasks = [("🧠", "完成 5 題", "0 / 5", "+20 EXP"), ("🔍", "訂正 1 題", "0 / 1", "+50 🪙"), ("⏱️", "學習 20 分鐘", "0 / 20", "+1 🎫")]
    cols = st.columns(3)
    for col, (icon, title, progress, reward) in zip(cols, tasks):
        with col:
            st.markdown(f'<div class="card"><div style="font-size:1.7rem">{icon}</div><div class="card-title">{title}</div><div class="muted">{progress}</div><div style="margin-top:.7rem;font-weight:900;color:#2a9d5e">{reward}</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">探索 MedSlime</div>', unsafe_allow_html=True)
    nav("home")


def study_home():
    topbar()
    st.markdown('<div class="eyebrow">STUDY</div><div class="hero-title" style="font-size:2rem">你想怎麼學習呢？</div><div class="hero-copy">選擇適合你現在狀態的方式，MedSlime 陪你一起進步。</div>', unsafe_allow_html=True)
    st.write("")

    rows = [
        [("📄", "我有教材", "上傳 PDF 教材，讓 AI 幫你整理重點並生成測驗。", "study_material_intro"), ("🧪", "我要刷國考", "練習歷屆國考題目，快速檢測實力與弱點。", None)],
        [("📘", "我要複習錯題", "回顧答錯或不確定的題目，加強你的弱點。", None), ("⏱️", "我要專心讀書", "進入專注計時器，累積今天的學習效率。", None)],
    ]
    for row in rows:
        cols = st.columns(2, gap="large")
        for col, (icon, title, copy, target) in zip(cols, row):
            with col:
                st.markdown(f'<div class="choice-card"><div class="choice-icon">{icon}</div><div class="choice-title">{title}</div><div class="choice-copy">{copy}</div></div>', unsafe_allow_html=True)
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
    st.markdown('<div class="intro-wrap"><div class="intro-slime">🟢📚</div><div class="hero-title" style="font-size:2rem">上傳教材，AI 幫你整理重點<br>並生成專屬測驗。</div><div class="hero-copy" style="max-width:680px;margin:.8rem auto">先不用把整份教材硬啃完。MedSlime 會先抓重點，再用題目幫你找出真正需要花時間的地方。</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="check-list"><div class="check-item">✅ 快速擷取教材重點</div><div class="check-item">✅ 生成適合複習的選擇題</div><div class="check-item">✅ 標記不確定與答錯觀念</div><div class="check-item">✅ 把需要加強的內容留下來</div></div>', unsafe_allow_html=True)
    if st.button("☁️ 上傳教材開始學習", type="primary", use_container_width=True):
        goto("study_material_upload")
    nav("study")


def study_material_upload():
    topbar()
    if st.button("← 返回介紹", key="upload_back"):
        goto("study_material_intro")
    st.markdown('<div class="eyebrow">YOUR MATERIAL</div><div class="hero-title" style="font-size:2rem">上傳你的教材</div><div class="hero-copy">目前先支援 PDF。建議使用含有可選取文字的檔案。</div>', unsafe_allow_html=True)
    st.write("")
    st.markdown('<div class="upload-box">', unsafe_allow_html=True)
    uploaded = st.file_uploader("選擇 PDF 教材", type=["pdf"], key="medslime_material_pdf")
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded is not None:
        st.session_state.uploaded_learning_file = uploaded.name
        size_mb = len(uploaded.getvalue()) / (1024 * 1024)
        st.success(f"已選擇：{uploaded.name} · {size_mb:.1f} MB")
        st.info("這一版先完成新的 MedSlime 上傳流程。下一步會把原本 study-tool 的 PDF 解析與 AI 出題邏輯接到這顆按鈕後面。")
        st.button("✨ 開始 AI 分析", type="primary", use_container_width=True, disabled=True)
    else:
        st.caption("小提醒：掃描型 PDF 或大量圖片頁面，之後需要另外處理圖片辨識。")
    nav("study")


def slime_page():
    topbar(); st.markdown("## 🐾 我的史萊姆")
    left, right = st.columns([1, 1.35], gap="large")
    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True); slime_card()
        st.session_state.slime_name = st.text_input("史萊姆名字", value=st.session_state.slime_name, max_chars=16)
        st.markdown('</div>', unsafe_allow_html=True)
    with right:
        st.markdown("### 收藏")
        for slime in st.session_state.collection:
            if st.button(("✅ " if slime == st.session_state.selected_slime else "🟢 ") + slime, key=f"slime_{slime}", use_container_width=True):
                st.session_state.selected_slime = slime; st.rerun()
    nav("slime")


def achievements_page():
    topbar(); st.markdown("## 🏆 成就")
    unlocked = set(st.session_state.unlocked_achievements)
    st.caption(f"目前解鎖 {len(unlocked)} / {len(ACHIEVEMENTS)}")
    cols = st.columns(3)
    for i, (aid, icon, title, desc, reward) in enumerate(ACHIEVEMENTS):
        css = "card" if aid in unlocked else "card locked"
        status = "已解鎖" if aid in unlocked else "尚未解鎖"
        with cols[i % 3]:
            st.markdown(f'<div class="{css}"><div style="font-size:2rem">{icon}</div><div class="card-title">{title}</div><div class="muted">{desc}</div><div style="margin-top:.6rem;font-weight:850">{status} · {reward}</div></div><br>', unsafe_allow_html=True)
    nav("achievements")


def gacha_page():
    topbar(); st.markdown("## 🎰 史萊姆召喚"); st.caption("1 張抽卡券 = 1 次召喚 · N 70% · R 25% · SSR 5%")
    if st.button("🎫 召喚一次", type="primary", use_container_width=True, disabled=st.session_state.tickets <= 0):
        st.session_state.tickets -= 1
        result = random.choices(GACHA_POOL, weights=[x["weight"] for x in GACHA_POOL], k=1)[0]
        duplicate = result["name"] in st.session_state.collection
        if duplicate:
            st.session_state.coins += 50 if result["rarity"] == "N" else 120 if result["rarity"] == "R" else 300
        else:
            st.session_state.collection.append(result["name"])
        st.session_state.last_gacha = {**result, "duplicate": duplicate}; st.rerun()
    result = st.session_state.last_gacha
    if result:
        msg = "重複獲得，已轉換成金幣" if result["duplicate"] else "NEW！已加入收藏"
        st.markdown(f'<div class="gacha-result"><div class="muted">{msg}</div><div style="font-size:5rem">{result["emoji"]}</div><div class="rarity-{result["rarity"]}">{result["rarity"]}</div><div class="card-title">{result["name"]}</div></div>', unsafe_allow_html=True)
    nav("gacha")


page = st.session_state.medslime_page
if page == "home": home()
elif page == "study": study_home()
elif page == "study_material_intro": study_material_intro()
elif page == "study_material_upload": study_material_upload()
elif page == "slime": slime_page()
elif page == "gacha": gacha_page()
elif page == "achievements": achievements_page()
else:
    st.session_state.medslime_page = "home"
    st.rerun()
