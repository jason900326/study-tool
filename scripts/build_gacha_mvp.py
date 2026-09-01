from pathlib import Path

p = Path('streamlit_app.py')
s = p.read_text(encoding='utf-8')

# 1) Add minimal gacha state.
needle = '    "last_gacha": None,\n'
insert = '    "last_gacha": None,\n    "gacha_pity": 0,\n    "gacha_free_date": None,\n'
assert needle in s
s = s.replace(needle, insert, 1)

# 2) Add a direct gacha entry on the slime collection page.
needle = '    st.markdown("## 史萊姆圖鑑")\n    st.caption("收集史萊姆、累積專屬碎片並解鎖外觀飾品。史萊姆只提供陪伴與展示，不提供能力 Buff。")\n'
insert = '''    title_col, gacha_col = st.columns([3, 1])\n    with title_col:\n        st.markdown("## 史萊姆圖鑑")\n        st.caption("收集史萊姆、累積專屬碎片並解鎖外觀飾品。史萊姆只提供陪伴與展示，不提供能力 Buff。")\n    with gacha_col:\n        st.button("🎰 去抽卡", type="primary", use_container_width=True, key="go_gacha_from_slime", on_click=set_page_without_extra_rerun, args=("gacha",))\n'''
assert needle in s
s = s.replace(needle, insert, 1)

# 3) Replace the old placeholder gacha page with a no-animation functional MVP.
start = s.index('def gacha_page():')
end = s.index('\n\nrender_quick_scroll_nav()', start)
new_page = r'''def gacha_page():
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
        @media(max-width:767px){.gacha-mvp-hero{padding:1rem}.gacha-mvp-title{font-size:1.45rem}.gacha-result-card{padding:1rem;border-radius:22px}}
        </style>
        """,
        unsafe_allow_html=True,
    )

    pity = int(st.session_state.get("gacha_pity", 0) or 0)
    today_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    free_available = st.session_state.get("gacha_free_date") != today_key

    st.markdown(
        f'<div class="gacha-mvp-hero"><div class="gacha-mvp-title">🎰 史萊姆召喚</div>'
        f'<div class="gacha-mvp-copy">先做最重要的事：按下去，真的抽到一隻史萊姆。暫時沒有翻牌動畫。</div>'
        f'<div class="gacha-mvp-pity">SSR 保底：{pity} / 100</div></div>',
        unsafe_allow_html=True,
    )
    st.caption("機率：N 32% · R 38% · SR 27% · SSR 3%　｜　所有抽法共用 100 抽 SSR 保底")

    def do_pull(payment):
        current_pity = int(st.session_state.get("gacha_pity", 0) or 0)
        if payment == "free":
            st.session_state.gacha_free_date = today_key
        elif payment == "coin":
            st.session_state.coins -= 100
        elif payment == "ticket":
            st.session_state.tickets -= 1

        # The 100th pull is forced SSR. Any earlier SSR resets the shared pity.
        force_ssr = current_pity >= 99
        if force_ssr:
            ssr_pool = [item for item in GACHA_POOL if item["rarity"] == "SSR"]
            result = random.choice(ssr_pool)
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

        if result["rarity"] == "SSR":
            st.session_state.gacha_pity = 0
        else:
            st.session_state.gacha_pity = current_pity + 1

        st.session_state.last_gacha = {
            **result,
            "duplicate": duplicate,
            "fragments": fragments,
            "payment": payment,
        }

    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        if st.button("🎁 今日免費 1 抽" if free_available else "✓ 今日免費已使用", type="primary", use_container_width=True, disabled=not free_available, key="gacha_free_pull"):
            do_pull("free")
            st.rerun()
    with c2:
        if st.button("🪙 100 金幣抽 1 次", use_container_width=True, disabled=st.session_state.coins < 100, key="gacha_coin_pull"):
            do_pull("coin")
            st.rerun()
    with c3:
        if st.button("🎫 1 張抽卡券抽 1 次", use_container_width=True, disabled=st.session_state.tickets <= 0, key="gacha_ticket_pull"):
            do_pull("ticket")
            st.rerun()

    st.caption(f"目前持有：🪙 {st.session_state.coins:,}　🎫 {st.session_state.tickets:,}")

    result = st.session_state.get("last_gacha")
    if result:
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
        st.button("🐾 去史萊姆圖鑑", use_container_width=True, key="gacha_to_collection", on_click=set_page_without_extra_rerun, args=("slime",))
'''
s = s[:start] + new_page + s[end:]

p.write_text(s, encoding='utf-8')
