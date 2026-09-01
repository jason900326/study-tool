from pathlib import Path

p = Path('streamlit_app.py')
s = p.read_text(encoding='utf-8')

# Defaults for one focus round record.
anchor = '    "focus_last_duration_minutes": 30,\n'
if '"focus_round_token": None' not in s:
    if anchor not in s:
        raise RuntimeError('focus defaults anchor not found')
    s = s.replace(anchor, anchor + '    "focus_round_token": None,\n    "focus_round_started_at": None,\n    "focus_round_start_coins": 0,\n', 1)

# Helpers before timer functions.
anchor = '\ndef _focus_elapsed_seconds():\n'
if 'def _focus_record_round(' not in s:
    if anchor not in s:
        raise RuntimeError('focus helper anchor not found')
    helpers = '''\ndef _focus_new_round_token():\n    seed = f"{_prototype_user_key()}|{time.time_ns()}|{random.random()}|{st.session_state.get('focus_round', 1)}"\n    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:40]\n\n\ndef _focus_record_round(elapsed_seconds, completed=False):\n    token = st.session_state.get("focus_round_token")\n    started_at = st.session_state.get("focus_round_started_at")\n    elapsed_seconds = max(0, int(elapsed_seconds or 0))\n    if not token or not started_at or elapsed_seconds <= 0:\n        return False\n    client = _achievement_supabase_client()\n    if not client:\n        return False\n    earned_coins = max(0, int(st.session_state.get("focus_session_coins", 0) or 0) - int(st.session_state.get("focus_round_start_coins", 0) or 0))\n    try:\n        client.table("focus_sessions").upsert({\n            "user_key": _prototype_user_key(),\n            "session_token": token,\n            "started_at": started_at,\n            "ended_at": datetime.now(timezone.utc).isoformat(),\n            "planned_minutes": max(1, int(st.session_state.get("focus_total_seconds", 0) or 0) // 60),\n            "focused_seconds": elapsed_seconds,\n            "earned_coins": earned_coins,\n            "completed": bool(completed),\n            "slime_name": st.session_state.get("selected_slime") or "綠色史萊姆",\n        }, on_conflict="user_key,session_token").execute()\n        return True\n    except Exception:\n        return False\n\n\ndef _focus_recent_sessions(limit=5):\n    client = _achievement_supabase_client()\n    if not client:\n        return []\n    try:\n        response = (\n            client.table("focus_sessions")\n            .select("started_at,focused_seconds,earned_coins,completed,slime_name")\n            .eq("user_key", _prototype_user_key())\n            .order("started_at", desc=True)\n            .limit(max(1, int(limit)))\n            .execute()\n        )\n        return response.data or []\n    except Exception:\n        return []\n\n'''
    s = s.replace(anchor, helpers + anchor, 1)

# Start each focus round with a fresh durable token.
old = '''    st.session_state.focus_end_at = time.time() + minutes * 60\n    st.session_state.focus_rewarded_blocks = 0\n'''
new = '''    st.session_state.focus_end_at = time.time() + minutes * 60\n    st.session_state.focus_rewarded_blocks = 0\n    st.session_state.focus_round_token = _focus_new_round_token()\n    st.session_state.focus_round_started_at = datetime.now(timezone.utc).isoformat()\n    st.session_state.focus_round_start_coins = int(st.session_state.get("focus_session_coins", 0) or 0)\n'''
if old not in s:
    raise RuntimeError('start focus anchor not found')
s = s.replace(old, new, 1)

# Stop: record before reset.
old = '''        st.session_state.focus_seconds_today += elapsed\n        st.session_state.focus_seconds_total += elapsed\n        _task_record_event(focus_seconds=elapsed)\n    reset_focus_timer()\n'''
new = '''        st.session_state.focus_seconds_today += elapsed\n        st.session_state.focus_seconds_total += elapsed\n        _task_record_event(focus_seconds=elapsed)\n        _focus_record_round(elapsed, completed=False)\n    reset_focus_timer()\n'''
if old not in s:
    raise RuntimeError('stop focus anchor not found')
s = s.replace(old, new, 1)

# Completion: record full completed round before switching to break.
old = '''            st.session_state.focus_seconds_today += st.session_state.focus_total_seconds\n            st.session_state.focus_seconds_total += st.session_state.focus_total_seconds\n            _task_record_event(focus_seconds=st.session_state.focus_total_seconds)\n            st.toast("🎉 這一輪專注完成！現在休息 5 分鐘。")\n'''
new = '''            st.session_state.focus_seconds_today += st.session_state.focus_total_seconds\n            st.session_state.focus_seconds_total += st.session_state.focus_total_seconds\n            _task_record_event(focus_seconds=st.session_state.focus_total_seconds)\n            _focus_record_round(st.session_state.focus_total_seconds, completed=True)\n            st.toast("🎉 這一輪專注完成！現在休息 5 分鐘。")\n'''
if old not in s:
    raise RuntimeError('focus complete anchor not found')
s = s.replace(old, new, 1)

# Clear round token after reset.
old = '''    st.session_state.focus_session_coins = 0\n    st.session_state.focus_round = 1\n'''
new = '''    st.session_state.focus_session_coins = 0\n    st.session_state.focus_round = 1\n    st.session_state.focus_round_token = None\n    st.session_state.focus_round_started_at = None\n    st.session_state.focus_round_start_coins = 0\n'''
# Only target reset function occurrence after its definition.
reset_start = s.index('def reset_focus_timer():')
reset_end = s.index('\ndef stop_focus_timer():', reset_start)
chunk = s[reset_start:reset_end]
if old not in chunk:
    raise RuntimeError('reset focus anchor not found')
chunk = chunk.replace(old, new, 1)
s = s[:reset_start] + chunk + s[reset_end:]

# Show recent durable focus history while idle.
old = '''            if st.button("🍅 開始專注", type="primary", use_container_width=True, key="focus_start"):\n                start_focus_round(minutes, new_session=True)\n                st.rerun()\n        return\n'''
new = '''            if st.button("🍅 開始專注", type="primary", use_container_width=True, key="focus_start"):\n                start_focus_round(minutes, new_session=True)\n                st.rerun()\n        recent = _focus_recent_sessions(5)\n        if recent:\n            st.markdown('<div class="section-title">最近專注</div>', unsafe_allow_html=True)\n            for row in recent:\n                seconds = max(0, int(row.get("focused_seconds", 0) or 0))\n                minutes_done = seconds // 60\n                coins = max(0, int(row.get("earned_coins", 0) or 0))\n                status = "完成" if row.get("completed") else "提前結束"\n                started = str(row.get("started_at") or "").replace("T", " ")[:16]\n                st.markdown(\n                    f'<div class="result-card"><strong>{minutes_done} 分鐘</strong> · {status}　<span class="muted">{html.escape(started)}</span><br><span class="muted">獲得 {coins} 🪙</span></div>',\n                    unsafe_allow_html=True,\n                )\n        return\n'''
if old not in s:
    raise RuntimeError('focus idle block anchor not found')
s = s.replace(old, new, 1)

p.write_text(s, encoding='utf-8')
