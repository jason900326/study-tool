from pathlib import Path

p = Path('streamlit_app.py')
s = p.read_text(encoding='utf-8')

# 1) Make slime progress backward/forward compatible so changing companions never crashes.
old = '''def get_slime_progress(name):
    progress = st.session_state.slime_progress
    if name not in progress:
        progress[name] = {"level": 1, "exp": 0, "fragments": 0}
    return progress[name]
'''
new = '''def get_slime_progress(name):
    progress = st.session_state.slime_progress
    item = progress.setdefault(name, {})
    # Legacy fields stay safe during the Streamlit prototype, even though Lv/EXP
    # are no longer part of the current MedSlime game design.
    item.setdefault("level", 1)
    item.setdefault("exp", 0)
    item.setdefault("fragments", 0)
    return item
'''
assert old in s
s = s.replace(old, new, 1)

# 2) Remove legacy Lv/EXP rendering from the home companion card.
old = '''    companion_progress = get_slime_progress(st.session_state.selected_slime)
    companion_nickname = get_slime_nickname(st.session_state.selected_slime)
'''
new = '''    get_slime_progress(st.session_state.selected_slime)
    companion_nickname = get_slime_nickname(st.session_state.selected_slime)
'''
assert old in s
s = s.replace(old, new, 1)
old = '''        st.markdown('<div class="home-slime-card">' + slime_avatar_markup(companion_item, size="home") + f'<div class="home-slime-label">{html.escape(companion_nickname)} · Lv.{companion_progress["level"]}</div><div class="home-xp"><div class="home-xp-fill" style="width:{min(100, companion_progress["exp"])}%"></div></div><div class="muted">{companion_progress["exp"]} / 100 EXP · {st.session_state.selected_slime}</div></div>', unsafe_allow_html=True)
'''
new = '''        st.markdown('<div class="home-slime-card">' + slime_avatar_markup(companion_item, size="home") + f'<div class="home-slime-label">{html.escape(companion_nickname)}</div><div class="muted">{html.escape(st.session_state.selected_slime)} · 陪伴中</div></div>', unsafe_allow_html=True)
'''
assert old in s
s = s.replace(old, new, 1)

# 3) Add a navigation helper that clears old gacha results whenever the user leaves/enters the gacha page.
anchor = '''def set_page_without_extra_rerun(page):
    st.session_state.medslime_page = page
    st.session_state.menu_open = False


def render_back_button(label, target, key):
'''
replacement = '''def set_page_without_extra_rerun(page):
    st.session_state.medslime_page = page
    st.session_state.menu_open = False


def open_fresh_gacha():
    st.session_state.last_gacha = None
    st.session_state.last_gacha_results = []
    st.session_state.medslime_page = "gacha"
    st.session_state.menu_open = False


def leave_gacha_to_collection():
    st.session_state.last_gacha = None
    st.session_state.last_gacha_results = []
    st.session_state.medslime_page = "slime"
    st.session_state.menu_open = False


def render_back_button(label, target, key):
'''
assert anchor in s
s = s.replace(anchor, replacement, 1)

# 4) Always open the gacha page fresh from the collection.
old = 'st.button("🎰 去抽卡", type="primary", use_container_width=True, key="go_gacha_from_slime", on_click=set_page_without_extra_rerun, args=("gacha",))'
new = 'st.button("🎰 去抽卡", type="primary", use_container_width=True, key="go_gacha_from_slime", on_click=open_fresh_gacha)'
assert old in s
s = s.replace(old, new, 1)

# 5) Replace the gacha MVP with single + 10-pull testing version.
start = s.index('def gacha_page():')
end = s.index('\n\nrender_quick_scroll_nav()', start)
new_gacha = r'''def gacha_page():
    # Temporary QA mode: effectively unlimited resources for gacha testing.
    st.session_state.coins = 999_999
    st.session_state.tickets = 999_999
    st.session_state.setdefault("last_gacha_results", [])

    topbar()
    render_back_button("返回我的史萊姆", "slime", "back_gacha")
    st.markdown(
        """
        <style>
        .gacha-mvp-hero{border:1px solid #dbe9e1;background:rgba(255,255,255,.92);border-radius:24px;padding:1.25rem 1.35rem;margin:.4rem 0 1rem;box-shadow:0 12px 28px rgba(32,85,54,.06)}
        .gacha-mvp-title{font-size:1.75rem;font-weight:950;color:#17372a;letter-spacing:-.03em}.gacha-mvp-copy{color:#789083;margin-top:.35rem;line-height:1.55}
        .gacha-mvp-pity{display:inline-flex;margin-top:.75rem;padding:.35rem .7rem;border-radius:999px;background:#f2f8f4;color:#315b45;font-size:.78rem;font-weight:850}
        .gacha-result-card{border:1px solid #d7e8df;background:rgba(255,255,255,.97);border-radius:28px;padding:1.4rem;text-align:center;margin:1.1rem auto 0;max-width:520px;box-shadow:0 16px 36px rgba(32,85,54,.10)}
        .gacha-result-card .official-slime-art-home,.gacha-result-card .catalog-slime-home{margin:0 auto}.gacha-result-rarity{font-weight:950;font-size:.8rem;color:#57a976;margin-top:.55rem}.gacha-result-name{font-size:1.45rem;font-weight:950;color:#17372a;margin-top:.18rem}.gacha-result-msg{margin-top:.55rem;color:#607d6d;font-weight:800}.gacha-result-frag{margin-top:.35rem;color:#789083;font-size:.82rem}
        .gacha-ten-card{border:1px solid #dbe9e1;background:rgba(255,255,255,.96);border-radius:18px;padding:.7rem .55rem;text-align:center;min-height:205px}.gacha-ten-card .official-slime-art-card,.gacha-ten-card .catalog-slime-card{margin:0 auto}.gacha-ten-name{font-size:.82rem;font-weight:900;color:#17372a;margin-top:.3rem;min-height:2.2rem}.gacha-ten-meta{font-size:.7rem;color:#789083;margin-top:.2rem}.gacha-ten-new{font-size:.7rem;font-weight:900;color:#31915b;margin-top:.25rem}
        @media(max-width:767px){.gacha-mvp-hero{padding:1rem}.gacha-mvp-title{font-size:1.45rem}.gacha-result-card{padding:1rem;border-radius:22px}.gacha-ten-card{min-height:180px;padding:.55rem .35rem}}
        </style>
        """,
        unsafe_allow_html=True,
    )

    pity = int(st.session_state.get("gacha_pity", 0) or 0)
    today_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    free_available = st.session_state.get("gacha_free_date") != today_key

    st.markdown(
        f'<div class="gacha-mvp-hero"><div class="gacha-mvp-title">🎰 史萊姆召喚</div>'
        f'<div class="gacha-mvp-copy">測試版：單抽與 10 連都直接顯示結果，暫時沒有翻牌動畫。</div>'
        f'<div class="gacha-mvp-pity">SSR 保底：{pity} / 100</div></div>',
        unsafe_allow_html=True,
    )
    st.caption("機率：N 32% · R 38% · SR 27% · SSR 3%　｜　所有抽法共用 100 抽 SSR 保底")
    st.caption("🧪 測試模式：金幣與抽卡券暫時無限")

    def do_pull(payment):
        current_pity = int(st.session_state.get("gacha_pity", 0) or 0)
        if payment == "free":
            st.session_state.gacha_free_date = today_key
        elif payment == "coin":
            st.session_state.coins -= 100
        elif payment == "ticket":
            st.session_state.tickets -= 1

        force_ssr = current_pity >= 99
        if force_ssr:
            result = random.choice([item for item in GACHA_POOL if item["rarity"] == "SSR"])
        else:
            result = random.choices(GACHA_POOL, weights=[item["weight"] for item in GACHA_POOL], k=1)[0]

        duplicate = result["name"] in st.session_state.collection
        fragments = 0
        if duplicate:
            fragments = 10
            get_slime_progress(result["name"])["fragments"] += 10
        else:
            st.session_state.collection.append(result["name"])
            get_slime_progress(result["name"])
            get_slime_nickname(result["name"])

        st.session_state.gacha_pity = 0 if result["rarity"] == "SSR" else current_pity + 1
        return {**result, "duplicate": duplicate, "fragments": fragments, "payment": payment}

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        if st.button("🎁 今日免費 1 抽" if free_available else "✓ 今日免費已使用", type="primary", use_container_width=True, disabled=not free_available, key="gacha_free_pull"):
            result = do_pull("free")
            st.session_state.last_gacha = result
            st.session_state.last_gacha_results = [result]
            st.rerun()
    with c2:
        if st.button("🪙 100 金幣抽 1 次", use_container_width=True, key="gacha_coin_pull"):
            result = do_pull("coin")
            st.session_state.last_gacha = result
            st.session_state.last_gacha_results = [result]
            st.rerun()
    with c3:
        if st.button("🎫 1 張抽卡券抽 1 次", use_container_width=True, key="gacha_ticket_pull"):
            result = do_pull("ticket")
            st.session_state.last_gacha = result
            st.session_state.last_gacha_results = [result]
            st.rerun()

    t1, t2 = st.columns(2, gap="medium")
    with t1:
        if st.button("🪙 1,000 金幣 10 連抽", type="primary", use_container_width=True, key="gacha_coin_ten"):
            results = [do_pull("coin") for _ in range(10)]
            st.session_state.last_gacha = results[-1]
            st.session_state.last_gacha_results = results
            st.rerun()
    with t2:
        if st.button("🎫 10 張抽卡券 10 連抽", use_container_width=True, key="gacha_ticket_ten"):
            results = [do_pull("ticket") for _ in range(10)]
            st.session_state.last_gacha = results[-1]
            st.session_state.last_gacha_results = results
            st.rerun()

    st.caption(f"目前持有：🪙 {st.session_state.coins:,}　🎫 {st.session_state.tickets:,}")

    results = st.session_state.get("last_gacha_results") or []
    if len(results) == 1:
        result = results[0]
        item = SLIME_BY_NAME.get(result["name"], result)
        avatar = slime_avatar_markup(item, size="home")
        if result.get("duplicate"):
            message = "重複獲得"
            sub = f'+10 {html.escape(result["name"])}專屬碎片'
        else:
            message = "NEW！已加入收藏"
            sub = "現在可以到史萊姆圖鑑查看它"
        st.markdown(
            f'<div class="gacha-result-card">{avatar}<div class="gacha-result-rarity">{html.escape(result["rarity"])}</div>'
            f'<div class="gacha-result-name">{html.escape(result["name"])}</div><div class="gacha-result-msg">{message}</div>'
            f'<div class="gacha-result-frag">{sub}</div></div>',
            unsafe_allow_html=True,
        )
    elif len(results) == 10:
        st.markdown("### 10 連抽結果")
        for start_index in range(0, 10, 5):
            cols = st.columns(5, gap="small")
            for col, result in zip(cols, results[start_index:start_index + 5]):
                with col:
                    item = SLIME_BY_NAME.get(result["name"], result)
                    avatar = slime_avatar_markup(item, size="card")
                    status = "重複 · +10 碎片" if result.get("duplicate") else "NEW！"
                    st.markdown(
                        f'<div class="gacha-ten-card">{avatar}<div class="gacha-result-rarity">{html.escape(result["rarity"])}</div>'
                        f'<div class="gacha-ten-name">{html.escape(result["name"])}</div><div class="gacha-ten-new">{html.escape(status)}</div></div>',
                        unsafe_allow_html=True,
                    )

    if results:
        st.button("🐾 去史萊姆圖鑑", use_container_width=True, key="gacha_to_collection", on_click=leave_gacha_to_collection)
'''
s = s[:start] + new_gacha + s[end:]

p.write_text(s, encoding='utf-8')
