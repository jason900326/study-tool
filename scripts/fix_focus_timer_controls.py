from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

old_runner = '''def _focus_runner_markup(progress, resting=False):\n    progress = min(1.0, max(0.0, float(progress)))\n    left = 6 + progress * 87\n    fill = progress * 87\n    background = selected_slime_background()\n    resting_class = " resting" if resting else ""\n    sleep = '<span class="focus-sleep">💤</span>' if resting else ""\n    return (\n        '<div class="focus-path">'\n        f'<div class="focus-path-fill" style="width:{fill:.2f}%"></div>'\n        f'<div class="focus-runner{resting_class}" style="left:{left:.2f}%;background:{background}">'\n        f'{sleep}<div class="focus-runner-mouth"></div></div>'\n        '<div class="focus-finish">🏁</div></div>'\n    )\n'''
new_runner = '''def _focus_runner_markup(progress, resting=False, runner_progress=None):\n    progress = min(1.0, max(0.0, float(progress)))\n    if runner_progress is None:\n        runner_progress = progress\n    runner_progress = min(1.0, max(0.0, float(runner_progress)))\n    left = 6 + runner_progress * 87\n    fill = progress * 87\n    background = selected_slime_background()\n    resting_class = " resting" if resting else ""\n    sleep = '<span class="focus-sleep">💤</span>' if resting else ""\n    return (\n        '<div class="focus-path">'\n        f'<div class="focus-path-fill" style="width:{fill:.2f}%"></div>'\n        f'<div class="focus-runner{resting_class}" style="left:{left:.2f}%;background:{background}">'\n        f'{sleep}<div class="focus-runner-mouth"></div></div>'\n        '<div class="focus-finish">🏁</div></div>'\n    )\n'''
if old_runner not in text:
    raise RuntimeError('runner function anchor not found')
text = text.replace(old_runner, new_runner, 1)

old_dialog = '''        with left:\n            if st.button("繼續專注", use_container_width=True, key="focus_stop_cancel"):\n                st.rerun()\n        with right:\n            if st.button("停止", type="primary", use_container_width=True, key="focus_stop_confirm"):\n                stop_focus_timer()\n                st.rerun()\n'''
new_dialog = '''        with left:\n            if st.button("繼續專注", use_container_width=True, key="focus_stop_cancel"):\n                st.rerun(scope="app")\n        with right:\n            if st.button("停止", type="primary", use_container_width=True, key="focus_stop_confirm"):\n                stop_focus_timer()\n                st.rerun(scope="app")\n'''
if old_dialog not in text:
    raise RuntimeError('dialog button anchor not found')
text = text.replace(old_dialog, new_dialog, 1)

old_break = '''        else:\n            progress = 1.0 if status in ("running", "paused", "break_done") else 0.0\n            st.markdown(f'<div class="focus-phase">BREAK · 第 {st.session_state.focus_round} 輪完成</div><div class="focus-clock">{_format_clock(remaining)}</div>', unsafe_allow_html=True)\n            st.markdown('<div class="focus-sub">休息是番茄鐘的一部分。史萊姆也在終點喘口氣。</div>', unsafe_allow_html=True)\n            st.markdown(_focus_runner_markup(progress, resting=True), unsafe_allow_html=True)\n            st.markdown(f'<div class="focus-reward-note">休息時間不累積金幣　<span class="focus-earned">這次已獲得 {st.session_state.focus_session_coins} 🪙</span></div>', unsafe_allow_html=True)\n'''
new_break = '''        else:\n            # During break, the slime stays at the finish line while the green bar\n            # shrinks from right to left, revealing white space as rest time passes.\n            break_fill = min(1.0, max(0.0, remaining / total)) if status in ("running", "paused") else 0.0\n            st.markdown(f'<div class="focus-phase">BREAK · 第 {st.session_state.focus_round} 輪完成</div><div class="focus-clock">{_format_clock(remaining)}</div>', unsafe_allow_html=True)\n            st.markdown('<div class="focus-sub">休息是番茄鐘的一部分。史萊姆也在終點喘口氣。</div>', unsafe_allow_html=True)\n            st.markdown(_focus_runner_markup(break_fill, resting=True, runner_progress=1.0), unsafe_allow_html=True)\n            st.markdown(f'<div class="focus-reward-note">休息時間不累積金幣　<span class="focus-earned">這次已獲得 {st.session_state.focus_session_coins} 🪙</span></div>', unsafe_allow_html=True)\n'''
if old_break not in text:
    raise RuntimeError('break progress anchor not found')
text = text.replace(old_break, new_break, 1)

old_stop = '''        with middle:\n            if st.button("■ 停止", use_container_width=True, key=f"focus_stop_{phase}"):\n                show_focus_stop_confirmation()\n'''
new_stop = '''        with middle:\n            if st.button("■ 停止", use_container_width=True, key=f"focus_stop_{phase}"):\n                # A dialog opened directly from a fragment becomes nested fragment UI,\n                # which can make its own buttons unresponsive. Request an app-level\n                # rerun and let focus_timer_page open the dialog outside the fragment.\n                st.session_state.focus_stop_requested = True\n                st.rerun(scope="app")\n'''
if old_stop not in text:
    raise RuntimeError('stop button anchor not found')
text = text.replace(old_stop, new_stop, 1)

old_page_end = '''        return\n\n    render_focus_timer_fragment()\n\n\n# =========================================================\n# Mistake bank\n'''
new_page_end = '''        return\n\n    # Open the confirmation dialog at app level, not from inside st.fragment.\n    # Pop first so dismissing with X will not cause it to reopen later.\n    if st.session_state.pop("focus_stop_requested", False):\n        show_focus_stop_confirmation()\n\n    render_focus_timer_fragment()\n\n\n# =========================================================\n# Mistake bank\n'''
if old_page_end not in text:
    raise RuntimeError('focus page end anchor not found')
text = text.replace(old_page_end, new_page_end, 1)

path.write_text(text, encoding='utf-8')
print('fixed focus stop dialog and break progress')
