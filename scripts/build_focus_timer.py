from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

# Timer needs wall-clock timestamps so it stays accurate across fragment reruns.
if 'import time\n' not in text:
    text = text.replace('import re\n', 'import re\nimport time\n', 1)

state_anchor = '    "mistake_subject": None,\n'
state_block = state_anchor + '''    "focus_status": "idle",\n    "focus_phase": "focus",\n    "focus_total_seconds": 1500,\n    "focus_remaining_seconds": 1500,\n    "focus_end_at": None,\n    "focus_rewarded_blocks": 0,\n    "focus_session_coins": 0,\n    "focus_seconds_today": 0,\n    "focus_round": 1,\n    "focus_last_duration_minutes": 25,\n'''
if '    "focus_status": "idle",\n' not in text:
    if state_anchor not in text:
        raise RuntimeError('default state anchor not found')
    text = text.replace(state_anchor, state_block, 1)

# Add focus timer styles before the generic slime styles.
css_anchor = '    .slime { width:178px; height:142px; margin:0 auto 1rem;'
css = r'''    /* Pomodoro focus timer */
    [class*="st-key-focus_setup_card"], [class*="st-key-focus_timer_card"] { max-width:880px; margin:.7rem auto 1rem; background:rgba(255,255,255,.94); border:1px solid #dceae2; border-radius:28px; padding:1.4rem 1.5rem 1.5rem; box-shadow:0 16px 38px rgba(30,82,51,.055); }
    .focus-clock { text-align:center; color:#143629; font-size:5.2rem; line-height:1; font-weight:950; letter-spacing:-.055em; margin:.75rem 0 .45rem; font-variant-numeric:tabular-nums; }
    .focus-phase { text-align:center; color:#2aa665; font-size:.88rem; font-weight:950; letter-spacing:.05em; text-transform:uppercase; }
    .focus-sub { text-align:center; color:#6d8779; line-height:1.55; margin:.2rem 0 1rem; }
    .focus-path { position:relative; height:126px; margin:1.1rem .45rem .8rem; border-radius:24px; background:linear-gradient(180deg,#f8fcf9,#eff8f3); border:1px solid #dcebe2; overflow:hidden; }
    .focus-path::after { content:""; position:absolute; left:4%; right:5%; bottom:25px; height:5px; border-radius:999px; background:#dce9df; }
    .focus-path-fill { position:absolute; left:4%; bottom:25px; height:5px; max-width:91%; border-radius:999px; background:linear-gradient(90deg,#60d790,#31c978); z-index:1; transition:width .8s linear; }
    .focus-finish { position:absolute; right:3.5%; bottom:33px; font-size:1.45rem; z-index:2; }
    .focus-runner { position:absolute; bottom:34px; width:70px; height:55px; border-radius:50% 50% 40% 40%/62% 62% 38% 38%; transform:translateX(-50%); box-shadow:inset -7px -9px 0 rgba(20,70,45,.08),0 8px 15px rgba(35,118,69,.13); z-index:4; transition:left .85s linear; animation:focusHop .65s ease-in-out infinite; }
    .focus-runner::before,.focus-runner::after { content:""; position:absolute; top:22px; width:6px; height:9px; border-radius:50%; background:#173b2b; }
    .focus-runner::before { left:20px; }
    .focus-runner::after { right:20px; }
    .focus-runner-mouth { position:absolute; left:27px; top:32px; width:17px; height:7px; border-bottom:2px solid #173b2b; border-radius:0 0 50% 50%; }
    .focus-runner.resting { animation:focusRest 1.5s ease-in-out infinite; }
    .focus-sleep { position:absolute; left:68%; top:-20px; font-size:1.1rem; }
    .focus-reward-note { text-align:center; color:#789083; font-size:.84rem; margin-top:.35rem; }
    .focus-earned { display:inline-flex; align-items:center; justify-content:center; padding:.3rem .7rem; border-radius:999px; background:#eef9f2; color:#238a53; font-weight:900; }
    .focus-done-card { text-align:center; padding:1rem .4rem .3rem; }
    .focus-done-title { color:#173b2b; font-size:1.55rem; font-weight:950; margin:.25rem 0; }
    @keyframes focusHop { 0%,100% { transform:translateX(-50%) translateY(0) scaleX(1.03); } 45% { transform:translateX(-50%) translateY(-10px) scaleX(.96); } 65% { transform:translateX(-50%) translateY(-5px) scaleX(1.04); } }
    @keyframes focusRest { 0%,100% { transform:translateX(-50%) translateY(0) scaleX(1.04) scaleY(.94); } 50% { transform:translateX(-50%) translateY(2px) scaleX(1.07) scaleY(.91); } }

'''
if '.focus-clock {' not in text:
    if css_anchor not in text:
        raise RuntimeError('focus CSS anchor not found')
    text = text.replace(css_anchor, css + css_anchor, 1)

# Mobile clock sizing.
mobile_anchor = '        .hero-title { font-size:1.9rem; }\n'
mobile_new = mobile_anchor + '        .focus-clock { font-size:3.8rem; }\n        .focus-path { height:108px; margin-left:0; margin-right:0; }\n        .focus-runner { width:60px; height:47px; }\n        .focus-runner::before,.focus-runner::after { top:19px; width:5px; height:8px; }\n        .focus-runner::before { left:17px; }\n        .focus-runner::after { right:17px; }\n        .focus-runner-mouth { left:23px; top:28px; width:15px; }\n'
if '        .focus-clock { font-size:3.8rem; }\n' not in text:
    if mobile_anchor not in text:
        raise RuntimeError('mobile focus anchor not found')
    text = text.replace(mobile_anchor, mobile_new, 1)

# Selected slime colors are also used by the moving focus companion.
slime_anchor = '''def slime_markup():\n    return '<div class="slime"><div class="shine"></div><div class="mouth"></div></div>'\n\n\n'''
slime_helpers = r'''def slime_markup():
    return '<div class="slime"><div class="shine"></div><div class="mouth"></div></div>'


def selected_slime_background():
    palettes = {
        "青蘋果史萊姆": "linear-gradient(145deg,#9bedad,#48c878)",
        "薄荷史萊姆": "linear-gradient(145deg,#b6f2d7,#58cba1)",
        "藍莓史萊姆": "linear-gradient(145deg,#a9d8ff,#5798e6)",
        "葡萄史萊姆": "linear-gradient(145deg,#d9b7ff,#9a67d8)",
        "黃金史萊姆": "linear-gradient(145deg,#ffe78b,#e6b83f)",
        "星空史萊姆": "linear-gradient(145deg,#8e8eea,#514d9d)",
    }
    return palettes.get(st.session_state.selected_slime, palettes["青蘋果史萊姆"])


'''
if 'def selected_slime_background():' not in text:
    if slime_anchor not in text:
        raise RuntimeError('slime helper anchor not found')
    text = text.replace(slime_anchor, slime_helpers, 1)

# Make the study card live.
old_focus_card = '("⏱️", "我要專心讀書", "進入專注計時器，累積今天的學習效率。", None)'
new_focus_card = '("⏱️", "我要專心讀書", "用番茄鐘陪你專注，完成每一小段就累積學習時間。", "focus_timer")'
if old_focus_card not in text:
    raise RuntimeError('focus study card anchor not found')
text = text.replace(old_focus_card, new_focus_card, 1)

# Make the home focus task reflect actual focused minutes in this session.
old_tasks = '''    tasks = [\n        ("🧠", "完成 5 題", "0 / 5", "+20 EXP"),\n        ("🔍", "訂正 1 題", "0 / 1", "+50 🪙"),\n        ("⏱️", "學習 20 分鐘", "0 / 20", "+1 🎫"),\n    ]\n'''
new_tasks = '''    focused_minutes = min(20, int(st.session_state.focus_seconds_today // 60))\n    tasks = [\n        ("🧠", "完成 5 題", "0 / 5", "+20 EXP"),\n        ("🔍", "訂正 1 題", "0 / 1", "+50 🪙"),\n        ("⏱️", "學習 20 分鐘", f"{focused_minutes} / 20", "+1 🎫"),\n    ]\n'''
if old_tasks not in text:
    raise RuntimeError('home tasks anchor not found')
text = text.replace(old_tasks, new_tasks, 1)

# Insert the full Pomodoro implementation before the mistake bank section.
ui_anchor = '''# =========================================================\n# Mistake bank\n# =========================================================\n'''
focus_code = r'''# =========================================================
# Focus timer / Pomodoro
# =========================================================

FOCUS_COINS_PER_BLOCK = 2
FOCUS_REWARD_BLOCK_SECONDS = 5 * 60
FOCUS_BREAK_SECONDS = 5 * 60


def _timer_remaining_seconds():
    if st.session_state.focus_status == "running" and st.session_state.focus_end_at:
        return max(0, int(round(st.session_state.focus_end_at - time.time())))
    return max(0, int(st.session_state.focus_remaining_seconds or 0))


def _focus_elapsed_seconds():
    total = max(0, int(st.session_state.focus_total_seconds or 0))
    return max(0, total - _timer_remaining_seconds())


def _award_focus_blocks(elapsed_seconds, toast=True):
    completed_blocks = max(0, int(elapsed_seconds // FOCUS_REWARD_BLOCK_SECONDS))
    new_blocks = completed_blocks - int(st.session_state.focus_rewarded_blocks or 0)
    if new_blocks <= 0:
        return
    earned = new_blocks * FOCUS_COINS_PER_BLOCK
    st.session_state.focus_rewarded_blocks = completed_blocks
    st.session_state.focus_session_coins += earned
    st.session_state.coins += earned
    if toast:
        st.toast(f"專注滿 {completed_blocks * 5} 分鐘，+{earned} 🪙")


def start_focus_round(minutes, new_session=False):
    minutes = max(5, int(minutes))
    if new_session:
        st.session_state.focus_session_coins = 0
        st.session_state.focus_round = 1
    st.session_state.focus_last_duration_minutes = minutes
    st.session_state.focus_phase = "focus"
    st.session_state.focus_status = "running"
    st.session_state.focus_total_seconds = minutes * 60
    st.session_state.focus_remaining_seconds = minutes * 60
    st.session_state.focus_end_at = time.time() + minutes * 60
    st.session_state.focus_rewarded_blocks = 0


def start_break():
    st.session_state.focus_phase = "break"
    st.session_state.focus_status = "running"
    st.session_state.focus_total_seconds = FOCUS_BREAK_SECONDS
    st.session_state.focus_remaining_seconds = FOCUS_BREAK_SECONDS
    st.session_state.focus_end_at = time.time() + FOCUS_BREAK_SECONDS


def start_next_focus_round():
    st.session_state.focus_round += 1
    start_focus_round(st.session_state.focus_last_duration_minutes, new_session=False)


def pause_focus_timer():
    if st.session_state.focus_status != "running":
        return
    st.session_state.focus_remaining_seconds = _timer_remaining_seconds()
    st.session_state.focus_end_at = None
    st.session_state.focus_status = "paused"


def resume_focus_timer():
    if st.session_state.focus_status != "paused":
        return
    remaining = max(1, int(st.session_state.focus_remaining_seconds or 0))
    st.session_state.focus_end_at = time.time() + remaining
    st.session_state.focus_status = "running"


def reset_focus_timer():
    st.session_state.focus_status = "idle"
    st.session_state.focus_phase = "focus"
    st.session_state.focus_total_seconds = st.session_state.focus_last_duration_minutes * 60
    st.session_state.focus_remaining_seconds = st.session_state.focus_total_seconds
    st.session_state.focus_end_at = None
    st.session_state.focus_rewarded_blocks = 0
    st.session_state.focus_session_coins = 0
    st.session_state.focus_round = 1


def stop_focus_timer():
    if st.session_state.focus_phase == "focus" and st.session_state.focus_status in ("running", "paused"):
        elapsed = _focus_elapsed_seconds()
        _award_focus_blocks(elapsed, toast=False)
        st.session_state.focus_seconds_today += elapsed
    reset_focus_timer()


def _format_clock(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def _focus_runner_markup(progress, resting=False):
    progress = min(1.0, max(0.0, float(progress)))
    left = 6 + progress * 87
    fill = progress * 87
    background = selected_slime_background()
    resting_class = " resting" if resting else ""
    sleep = '<span class="focus-sleep">💤</span>' if resting else ""
    return (
        '<div class="focus-path">'
        f'<div class="focus-path-fill" style="width:{fill:.2f}%"></div>'
        f'<div class="focus-runner{resting_class}" style="left:{left:.2f}%;background:{background}">'
        f'{sleep}<div class="focus-runner-mouth"></div></div>'
        '<div class="focus-finish">🏁</div></div>'
    )


def show_focus_stop_confirmation():
    @st.dialog("停止這次專注嗎？")
    def _dialog():
        st.write("已完成的專注時間與已拿到的金幣會保留；尚未滿 5 分鐘的區段不會另外給金幣。")
        left, right = st.columns(2)
        with left:
            if st.button("繼續專注", use_container_width=True, key="focus_stop_cancel"):
                st.rerun()
        with right:
            if st.button("停止", type="primary", use_container_width=True, key="focus_stop_confirm"):
                stop_focus_timer()
                st.rerun()
    _dialog()


@st.fragment(run_every=1)
def render_focus_timer_fragment():
    phase = st.session_state.focus_phase
    status = st.session_state.focus_status
    remaining = _timer_remaining_seconds()

    if phase == "focus" and status == "running":
        elapsed = _focus_elapsed_seconds()
        _award_focus_blocks(elapsed)
        if remaining <= 0:
            _award_focus_blocks(st.session_state.focus_total_seconds)
            st.session_state.focus_seconds_today += st.session_state.focus_total_seconds
            st.toast("🎉 這一輪專注完成！現在休息 5 分鐘。")
            start_break()
            st.rerun()

    if phase == "break" and status == "running" and remaining <= 0:
        st.session_state.focus_remaining_seconds = 0
        st.session_state.focus_end_at = None
        st.session_state.focus_status = "break_done"
        st.rerun()

    phase = st.session_state.focus_phase
    status = st.session_state.focus_status
    remaining = _timer_remaining_seconds()
    total = max(1, int(st.session_state.focus_total_seconds or 1))

    with st.container(key="focus_timer_card"):
        if phase == "focus":
            elapsed = max(0, total - remaining)
            progress = min(1.0, elapsed / total)
            st.markdown(f'<div class="focus-phase">FOCUS · 第 {st.session_state.focus_round} 輪</div><div class="focus-clock">{_format_clock(remaining)}</div>', unsafe_allow_html=True)
            paused_text = " · 已暫停" if status == "paused" else ""
            st.markdown(f'<div class="focus-sub">{st.session_state.selected_slime} 正陪你往終點前進{paused_text}</div>', unsafe_allow_html=True)
            st.markdown(_focus_runner_markup(progress, resting=status == "paused"), unsafe_allow_html=True)
            st.markdown(f'<div class="focus-reward-note">每完整 5 分鐘 +{FOCUS_COINS_PER_BLOCK} 🪙　<span class="focus-earned">這次已獲得 {st.session_state.focus_session_coins} 🪙</span></div>', unsafe_allow_html=True)
        else:
            progress = 1.0 if status in ("running", "paused", "break_done") else 0.0
            st.markdown(f'<div class="focus-phase">BREAK · 第 {st.session_state.focus_round} 輪完成</div><div class="focus-clock">{_format_clock(remaining)}</div>', unsafe_allow_html=True)
            st.markdown('<div class="focus-sub">休息是番茄鐘的一部分。史萊姆也在終點喘口氣。</div>', unsafe_allow_html=True)
            st.markdown(_focus_runner_markup(progress, resting=True), unsafe_allow_html=True)
            st.markdown(f'<div class="focus-reward-note">休息時間不累積金幣　<span class="focus-earned">這次已獲得 {st.session_state.focus_session_coins} 🪙</span></div>', unsafe_allow_html=True)

        if status == "break_done":
            st.markdown('<div class="focus-done-card"><div class="focus-done-title">休息完成，要再來一輪嗎？</div><div class="muted">下一輪會沿用剛剛的專注時間。</div></div>', unsafe_allow_html=True)
            left, right = st.columns(2)
            with left:
                if st.button("先結束", use_container_width=True, key="focus_break_finish"):
                    reset_focus_timer()
                    st.rerun()
            with right:
                if st.button("開始下一輪 →", type="primary", use_container_width=True, key="focus_next_round"):
                    start_next_focus_round()
                    st.rerun()
            return

        left, middle, right = st.columns(3)
        with left:
            if status == "running":
                if st.button("⏸ 暫停", use_container_width=True, key=f"focus_pause_{phase}"):
                    pause_focus_timer()
                    st.rerun()
            else:
                if st.button("▶ 繼續", type="primary", use_container_width=True, key=f"focus_resume_{phase}"):
                    resume_focus_timer()
                    st.rerun()
        with middle:
            if st.button("■ 停止", use_container_width=True, key=f"focus_stop_{phase}"):
                show_focus_stop_confirmation()
        with right:
            if phase == "break":
                if st.button("跳過休息 →", type="primary", use_container_width=True, key="focus_skip_break"):
                    start_next_focus_round()
                    st.rerun()
            else:
                st.button("休息 5 分鐘", use_container_width=True, disabled=True, key="focus_break_hint")


def focus_timer_page():
    topbar()
    render_back_button("返回學習", "study", "back_focus_timer")
    st.markdown('<div class="study-header"><div class="eyebrow">FOCUS</div><div class="hero-title" style="font-size:2.05rem">和史萊姆一起專心一下。</div><div class="hero-copy">完成一輪專注後會自動進入 5 分鐘休息；想直接繼續也可以跳過休息。</div></div>', unsafe_allow_html=True)

    if st.session_state.focus_status == "idle":
        with st.container(key="focus_setup_card"):
            st.markdown('<div class="card-title" style="font-size:1.15rem;margin-bottom:.75rem">這一輪要專注多久？</div>', unsafe_allow_html=True)
            choice = st.radio("專注時間", ["25 分鐘", "50 分鐘", "自訂"], horizontal=True, key="focus_duration_choice", label_visibility="collapsed")
            if choice == "自訂":
                minutes = st.number_input("自訂分鐘", min_value=5, max_value=120, value=int(st.session_state.focus_last_duration_minutes), step=5, key="focus_custom_minutes")
            else:
                minutes = 25 if choice == "25 分鐘" else 50
            st.markdown(f'<div class="focus-reward-note">目前暫定：每完整 5 分鐘 +{FOCUS_COINS_PER_BLOCK} 🪙。金幣經濟之後再一起平衡。</div>', unsafe_allow_html=True)
            if st.button("🍅 開始專注", type="primary", use_container_width=True, key="focus_start"):
                start_focus_round(minutes, new_session=True)
                st.rerun()
        return

    render_focus_timer_fragment()


'''
if 'def focus_timer_page():' not in text:
    if ui_anchor not in text:
        raise RuntimeError('mistake bank insertion anchor not found')
    text = text.replace(ui_anchor, focus_code + ui_anchor, 1)

# Add route.
route_anchor = '''elif page == "mistakes":\n    mistake_bank_page()\n'''
route_new = '''elif page == "focus_timer":\n    focus_timer_page()\nelif page == "mistakes":\n    mistake_bank_page()\n'''
if 'elif page == "focus_timer":\n' not in text:
    if route_anchor not in text:
        raise RuntimeError('focus route anchor not found')
    text = text.replace(route_anchor, route_new, 1)

path.write_text(text, encoding='utf-8')
print('built MedSlime Pomodoro focus timer')
