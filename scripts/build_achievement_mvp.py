from pathlib import Path
import re

p = Path('streamlit_app.py')
s = p.read_text(encoding='utf-8')

# ---- Session state ---------------------------------------------------------
state_anchor = '    "focus_seconds_today": 0,\n'
if state_anchor not in s:
    raise RuntimeError('focus_seconds_today state anchor not found')
s = s.replace(
    state_anchor,
    state_anchor + '    "focus_seconds_total": 0,\n    "gacha_pull_count": 0,\n    "achievement_claimed": {},\n    "achievement_unlocked_at": {},\n    "achievement_user_key": None,\n',
    1,
)

# ---- Replace old achievement definitions ---------------------------------
start = s.index('ACHIEVEMENTS = [')
end = s.index('\n\nSLIME_CATALOG = [', start)
new_defs = '''ACHIEVEMENTS = [
    {"id":"focus_1h","icon":"⏱️","title":"坐得住了","condition":"累積專注 1 小時","metric":"focus_hours","target":1,"reward_type":"coins","reward_amount":50},
    {"id":"focus_10h","icon":"📚","title":"開始認真","condition":"累積專注 10 小時","metric":"focus_hours","target":10,"reward_type":"coins","reward_amount":100},
    {"id":"focus_30h","icon":"🪑","title":"屁股黏住了","condition":"累積專注 30 小時","metric":"focus_hours","target":30,"reward_type":"tickets","reward_amount":1},
    {"id":"focus_60h","icon":"🩺","title":"真正的備考生活","condition":"累積專注 60 小時","metric":"focus_hours","target":60,"reward_type":"coins","reward_amount":300},
    {"id":"focus_100h","icon":"🔥","title":"閉關修煉","condition":"累積專注 100 小時","metric":"focus_hours","target":100,"reward_type":"tickets","reward_amount":2},
    {"id":"focus_150h","icon":"🕳️","title":"時間黑洞","condition":"累積專注 150 小時","metric":"focus_hours","target":150,"reward_type":"tickets","reward_amount":3},
    {"id":"collect_3","icon":"🟢","title":"開始收藏","condition":"擁有 3 隻史萊姆","metric":"collection","target":3,"reward_type":"coins","reward_amount":50},
    {"id":"collect_8","icon":"🧪","title":"史萊姆居民","condition":"擁有 8 隻史萊姆","metric":"collection","target":8,"reward_type":"coins","reward_amount":100},
    {"id":"collect_17","icon":"👑","title":"全圖鑑","condition":"收集全部 17 隻史萊姆","metric":"collection","target":17,"reward_type":"tickets","reward_amount":3},
    {"id":"gacha_10","icon":"🎰","title":"試試手氣","condition":"累積抽卡 10 次","metric":"gacha","target":10,"reward_type":"coins","reward_amount":50},
    {"id":"gacha_50","icon":"🎟️","title":"抽卡常客","condition":"累積抽卡 50 次","metric":"gacha","target":50,"reward_type":"tickets","reward_amount":1},
    {"id":"streak_3","icon":"🔥","title":"開始習慣","condition":"連續學習 3 天","metric":"streak","target":3,"reward_type":"coins","reward_amount":50},
]
'''
s = s[:start] + new_defs + s[end:]

# ---- Make focus time cumulative when today's seconds are incremented -------
pattern = re.compile(r'(?m)^(\s*)st\.session_state\.focus_seconds_today\s*\+=\s*(.+)$')

def add_total(match):
    indent, expr = match.group(1), match.group(2)
    return match.group(0) + f'\n{indent}st.session_state.focus_seconds_total += {expr}'

s, focus_patch_count = pattern.subn(add_total, s)

# ---- Count every gacha pull (10-pull calls do_pull ten times) -------------
gacha_pos = s.index('def gacha_page():')
gacha_anchor = '        current_pity = int(st.session_state.get("gacha_pity", 0) or 0)\n'
gacha_insert = gacha_anchor + '        st.session_state.gacha_pull_count = int(st.session_state.get("gacha_pull_count", 0) or 0) + 1\n'
pos = s.index(gacha_anchor, gacha_pos)
s = s[:pos] + s[pos:].replace(gacha_anchor, gacha_insert, 1)

# ---- Add achievement shortcut next to gacha on collection page ------------
header_old = '''    title_col, gacha_col = st.columns([3, 1])
    with title_col:
        st.markdown("## 史萊姆圖鑑")
        st.caption("收集史萊姆、累積專屬碎片並解鎖外觀飾品。史萊姆只提供陪伴與展示，不提供能力 Buff。")
    with gacha_col:
        st.button("🎰 去抽卡", type="primary", use_container_width=True, key="go_gacha_from_slime", on_click=open_fresh_gacha)
'''
header_new = '''    title_col, achievement_col, gacha_col = st.columns([3, 1, 1])
    with title_col:
        st.markdown("## 史萊姆圖鑑")
        st.caption("收集史萊姆、累積專屬碎片並解鎖外觀飾品。史萊姆只提供陪伴與展示，不提供能力 Buff。")
    with achievement_col:
        st.button("🏆 成就", use_container_width=True, key="go_achievements_from_slime", on_click=set_page_without_extra_rerun, args=("achievements",))
    with gacha_col:
        st.button("🎰 去抽卡", type="primary", use_container_width=True, key="go_gacha_from_slime", on_click=open_fresh_gacha)
'''
if header_old not in s:
    raise RuntimeError('slime header action anchor not found')
s = s.replace(header_old, header_new, 1)

# ---- Replace achievement page ---------------------------------------------
ach_start = s.index('def achievements_page():')
ach_end = s.index('\n\ndef render_quick_scroll_nav():', ach_start)
new_page = r'''def _achievement_supabase_client():
    """Best-effort client for the prototype; UI still works if the table is not ready."""
    try:
        url = None
        key = None
        for candidate in ("SUPABASE_URL", "supabase_url"):
            try:
                if candidate in st.secrets:
                    url = st.secrets[candidate]
                    break
            except Exception:
                pass
        for candidate in ("SUPABASE_KEY", "SUPABASE_ANON_KEY", "supabase_key", "supabase_anon_key"):
            try:
                if candidate in st.secrets:
                    key = st.secrets[candidate]
                    break
            except Exception:
                pass
        try:
            if "supabase" in st.secrets:
                section = st.secrets["supabase"]
                url = url or section.get("url") or section.get("URL")
                key = key or section.get("key") or section.get("anon_key") or section.get("KEY")
        except Exception:
            pass
        if url and key:
            return create_client(str(url), str(key))
    except Exception:
        pass
    return None


def _achievement_user_key():
    value = st.session_state.get("achievement_user_key")
    if not value:
        seed = f"{time.time_ns()}-{random.random()}-{st.session_state.get('slime_name','Medi')}"
        value = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]
        st.session_state.achievement_user_key = value
    return value


def _achievement_progress(item):
    metric = item["metric"]
    if metric == "focus_hours":
        # Keep today's already-earned seconds visible even for sessions created before this field existed.
        total_seconds = max(
            int(st.session_state.get("focus_seconds_total", 0) or 0),
            int(st.session_state.get("focus_seconds_today", 0) or 0),
        )
        return total_seconds / 3600
    if metric == "collection":
        return len(set(st.session_state.get("collection", [])))
    if metric == "gacha":
        return int(st.session_state.get("gacha_pull_count", 0) or 0)
    if metric == "streak":
        return int(st.session_state.get("streak", 0) or 0)
    return 0


def _achievement_progress_text(item, value):
    target = item["target"]
    if item["metric"] == "focus_hours":
        shown = f"{value:.1f}" if value < 10 and value % 1 else f"{int(value)}"
        return f"{shown} / {target} 小時"
    if item["metric"] == "collection":
        return f"{int(value)} / {target} 隻"
    if item["metric"] == "gacha":
        return f"{int(value)} / {target} 抽"
    if item["metric"] == "streak":
        return f"{int(value)} / {target} 天"
    return f"{value} / {target}"


def _achievement_reward_text(item):
    if item["reward_type"] == "coins":
        return f"🪙 {item['reward_amount']} 金幣"
    return f"🎫 抽卡券 ×{item['reward_amount']}"


def _achievement_sync_from_supabase():
    client = _achievement_supabase_client()
    if not client:
        return False
    try:
        response = (
            client.table("achievement_claims")
            .select("achievement_id,unlocked_at,claimed_at")
            .eq("user_key", _achievement_user_key())
            .execute()
        )
        for row in (response.data or []):
            aid = row.get("achievement_id")
            if not aid:
                continue
            if row.get("unlocked_at"):
                st.session_state.achievement_unlocked_at[aid] = row.get("unlocked_at")
            if row.get("claimed_at"):
                st.session_state.achievement_claimed[aid] = row.get("claimed_at")
        return True
    except Exception:
        return False


def _achievement_record_unlock(item):
    aid = item["id"]
    if aid in st.session_state.achievement_unlocked_at:
        return
    unlocked_at = datetime.now(timezone.utc).isoformat()
    st.session_state.achievement_unlocked_at[aid] = unlocked_at
    client = _achievement_supabase_client()
    if not client:
        return
    try:
        client.table("achievement_claims").upsert(
            {
                "user_key": _achievement_user_key(),
                "achievement_id": aid,
                "unlocked_at": unlocked_at,
                "claimed_at": None,
                "reward_type": item["reward_type"],
                "reward_amount": int(item["reward_amount"]),
            },
            on_conflict="user_key,achievement_id",
        ).execute()
    except Exception:
        pass


def _claim_achievement(item):
    aid = item["id"]
    progress = _achievement_progress(item)
    if progress < item["target"] or aid in st.session_state.achievement_claimed:
        return False, "這個成就目前不能領取。"

    client = _achievement_supabase_client()
    if client:
        try:
            existing = (
                client.table("achievement_claims")
                .select("claimed_at")
                .eq("user_key", _achievement_user_key())
                .eq("achievement_id", aid)
                .limit(1)
                .execute()
            )
            if existing.data and existing.data[0].get("claimed_at"):
                st.session_state.achievement_claimed[aid] = existing.data[0]["claimed_at"]
                return False, "這個獎勵已經領取過了。"
        except Exception:
            pass

    claimed_at = datetime.now(timezone.utc).isoformat()
    # Write the claim first when Supabase is ready. The unique constraint + claimed_at guard
    # prevents a second claim even if the UI is clicked again after reruns.
    if client:
        try:
            client.table("achievement_claims").upsert(
                {
                    "user_key": _achievement_user_key(),
                    "achievement_id": aid,
                    "unlocked_at": st.session_state.achievement_unlocked_at.get(aid, claimed_at),
                    "claimed_at": claimed_at,
                    "reward_type": item["reward_type"],
                    "reward_amount": int(item["reward_amount"]),
                },
                on_conflict="user_key,achievement_id",
            ).execute()
        except Exception as error:
            return False, f"Supabase 紀錄失敗，暫不發放獎勵：{type(error).__name__}"

    if item["reward_type"] == "coins":
        st.session_state.coins += int(item["reward_amount"])
    else:
        st.session_state.tickets += int(item["reward_amount"])
    st.session_state.achievement_claimed[aid] = claimed_at
    return True, f"已領取 {_achievement_reward_text(item)}"


def achievements_page():
    topbar()
    render_back_button("返回我的史萊姆", "slime", "back_achievements")
    st.markdown(
        """
        <style>
        .achievement-mvp-marker{display:none}.achievement-mvp-head{margin:.3rem 0 1rem}.achievement-mvp-title{font-size:2rem;font-weight:950;color:#17372a!important;letter-spacing:-.04em}.achievement-mvp-copy{margin-top:.25rem;color:#789083!important}
        .achievement-row{border:1px solid #dbe9e1;background:rgba(255,255,255,.94);border-radius:20px;padding:1rem 1.05rem;margin:.65rem 0 .25rem;box-shadow:0 8px 22px rgba(32,85,54,.05)}
        .achievement-row.done{border-color:#cde7d7;background:#fbfffc}.achievement-row.claimed{background:#f6faf7}.achievement-row-top{display:flex;justify-content:space-between;gap:.75rem;align-items:flex-start}.achievement-row-name{font-size:1.05rem;font-weight:950;color:#17372a!important}.achievement-row-condition{margin-top:.18rem;font-size:.82rem;color:#789083!important}.achievement-row-status{white-space:nowrap;border-radius:999px;padding:.28rem .58rem;font-size:.7rem;font-weight:900}.achievement-row-status.pending{background:#f2f4f3;color:#789083}.achievement-row-status.done{background:#e9f8ef;color:#28754b}.achievement-row-status.claimed{background:#edf4ef;color:#557768}.achievement-row-progressline{display:flex;justify-content:space-between;gap:.6rem;margin-top:.8rem;font-size:.76rem;color:#557768!important}.achievement-row-reward{font-weight:900;color:#315b45!important}.achievement-track{height:7px;background:#e6eee9;border-radius:999px;overflow:hidden;margin-top:.42rem}.achievement-fill{height:100%;background:#55b97b;border-radius:999px}
        [data-testid="stMainBlockContainer"]:has(.achievement-mvp-marker) h1,[data-testid="stMainBlockContainer"]:has(.achievement-mvp-marker) h2,[data-testid="stMainBlockContainer"]:has(.achievement-mvp-marker) h3,[data-testid="stMainBlockContainer"]:has(.achievement-mvp-marker) p,[data-testid="stMainBlockContainer"]:has(.achievement-mvp-marker) label{color:#244c39!important}
        @media(max-width:767px){.achievement-mvp-title{font-size:1.7rem}.achievement-row{padding:.85rem}.achievement-row-top{gap:.4rem}.achievement-row-status{font-size:.64rem;padding:.24rem .45rem}.achievement-row-progressline{flex-direction:column;gap:.15rem}}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="achievement-mvp-marker"></div>', unsafe_allow_html=True)
    st.markdown('<div class="achievement-mvp-head"><div class="achievement-mvp-title">🏆 成就</div><div class="achievement-mvp-copy">達成條件後即可領獎；已領取的成就不能重複領取。</div></div>', unsafe_allow_html=True)

    db_ready = _achievement_sync_from_supabase()

    completed_count = 0
    claimed_count = 0
    for item in ACHIEVEMENTS:
        value = _achievement_progress(item)
        if value >= item["target"]:
            completed_count += 1
            _achievement_record_unlock(item)
        if item["id"] in st.session_state.achievement_claimed:
            claimed_count += 1

    a, b, c = st.columns(3)
    a.metric("成就", f"{completed_count} / {len(ACHIEVEMENTS)}")
    b.metric("已領獎", claimed_count)
    c.metric("可領取", max(0, completed_count - claimed_count))
    if not db_ready:
        st.caption("Supabase 成就表尚未連上時，畫面與領獎仍可先用 session 測試；SQL 建表後會自動開始同步。")

    for item in ACHIEVEMENTS:
        aid = item["id"]
        value = _achievement_progress(item)
        completed = value >= item["target"]
        claimed = aid in st.session_state.achievement_claimed
        pct = max(0, min(100, round((value / item["target"]) * 100))) if item["target"] else 100
        if claimed:
            status_text, status_class, row_class = "✓ 已領獎", "claimed", "claimed"
        elif completed:
            status_text, status_class, row_class = "✓ 已完成", "done", "done"
        else:
            status_text, status_class, row_class = "尚未完成", "pending", ""

        st.markdown(
            f'<div class="achievement-row {row_class}"><div class="achievement-row-top">'
            f'<div><div class="achievement-row-name">{item["icon"]} {html.escape(item["title"])}</div>'
            f'<div class="achievement-row-condition">{html.escape(item["condition"])}</div></div>'
            f'<div class="achievement-row-status {status_class}">{status_text}</div></div>'
            f'<div class="achievement-row-progressline"><span>{html.escape(_achievement_progress_text(item, value))}</span>'
            f'<span class="achievement-row-reward">獎勵：{html.escape(_achievement_reward_text(item))}</span></div>'
            f'<div class="achievement-track"><div class="achievement-fill" style="width:{pct}%"></div></div></div>',
            unsafe_allow_html=True,
        )

        button_text = "已領取" if claimed else ("領取獎勵" if completed else "尚未完成")
        if st.button(
            button_text,
            key=f"claim_achievement_{aid}",
            type="primary" if completed and not claimed else "secondary",
            disabled=claimed or not completed,
            use_container_width=True,
        ):
            ok, message = _claim_achievement(item)
            if ok:
                st.toast(message, icon="🎁")
                st.rerun()
            else:
                st.warning(message)
'''
s = s[:ach_start] + new_page + s[ach_end:]

# ---- Ensure dispatcher has achievement route -------------------------------
if 'elif page == "achievements":' not in s:
    dispatcher_anchor = 'elif page == "slime":\n    slime_page()\n'
    if dispatcher_anchor not in s:
        raise RuntimeError('slime dispatcher anchor not found')
    s = s.replace(dispatcher_anchor, dispatcher_anchor + 'elif page == "achievements":\n    achievements_page()\n', 1)

p.write_text(s, encoding='utf-8')
print(f'achievement MVP patched; cumulative focus increments patched: {focus_patch_count}')
