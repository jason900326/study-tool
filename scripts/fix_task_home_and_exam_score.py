from pathlib import Path

p = Path('streamlit_app.py')
s = p.read_text(encoding='utf-8')

# 1) National exam score: 80 questions => 1.25 points each. Preserve exact decimal steps.
start = s.index('def national_exam_result_page():')
end = s.index('\ndef _queue_material_processing', start)
chunk = s[start:end]
old = '    score = round((correct / len(questions)) * 100) if questions else 0\n'
new = '    score = (correct / len(questions)) * 100 if questions else 0\n    score_text = f"{score:.2f}".rstrip("0").rstrip(".")\n'
if old not in chunk:
    raise RuntimeError('national exam score anchor not found')
chunk = chunk.replace(old, new, 1)
if '{score} / 100' not in chunk:
    raise RuntimeError('national exam score display anchor not found')
chunk = chunk.replace('{score} / 100', '{score_text} / 100', 1)
s = s[:start] + chunk + s[end:]

# 2) Home daily task cards: show claim state + claim button directly on home.
old_home = '''    _task_mark_active_day()\n    daily = _task_daily_snapshot()\n    cols = st.columns(3, gap="medium")\n    for col, task in zip(cols, DAILY_TASKS):\n        value = daily.get(task["metric"], 0)\n        progress = _task_progress_text(task, value)\n        reward = _task_reward_text(task)\n        done = value >= task["target"]\n        with col:\n            st.markdown(\n                f'<div class="home-task"><div class="task-icon">{task["icon"]}</div><div class="card-title">{html.escape(task["title"])}</div>'\n                f'<div class="muted">{html.escape(progress)}</div><div class="task-reward">{"✓ 已完成" if done else html.escape(reward)}</div></div>',\n                unsafe_allow_html=True,\n            )\n    if st.button("查看每日／每週任務", use_container_width=True, key="home_open_tasks"):\n        goto("tasks")\n'''
new_home = '''    _task_mark_active_day()\n    daily = _task_daily_snapshot()\n    daily_key = _task_day_key()\n    daily_claims = {row.get("task_id") for row in _task_claim_rows("daily", daily_key)}\n    cols = st.columns(3, gap="medium")\n    for col, task in zip(cols, DAILY_TASKS):\n        value = daily.get(task["metric"], 0)\n        progress = _task_progress_text(task, value)\n        reward = _task_reward_text(task)\n        done = value >= task["target"]\n        claimed = task["id"] in daily_claims\n        if claimed:\n            reward_line = "✓ 已領取"\n        elif done:\n            reward_line = f"✓ 已完成 · {reward}"\n        else:\n            reward_line = reward\n        with col:\n            st.markdown(\n                f'<div class="home-task"><div class="task-icon">{task["icon"]}</div><div class="card-title">{html.escape(task["title"])}</div>'\n                f'<div class="muted">{html.escape(progress)}</div><div class="task-reward">{html.escape(reward_line)}</div></div>',\n                unsafe_allow_html=True,\n            )\n            button_label = "已領取" if claimed else ("領取獎勵" if done else "尚未完成")\n            if st.button(\n                button_label,\n                key=f"home_claim_daily_{task['id']}",\n                disabled=claimed or not done,\n                use_container_width=True,\n                type="primary" if done and not claimed else "secondary",\n            ):\n                ok, message = _task_claim(task, "daily", daily_key, value)\n                if ok:\n                    st.toast(message, icon="🎁")\n                    st.rerun()\n                else:\n                    st.warning(message)\n    if st.button("查看每日／每週任務", use_container_width=True, key="home_open_tasks"):\n        goto("tasks")\n'''
if old_home not in s:
    raise RuntimeError('home daily task block not found')
s = s.replace(old_home, new_home, 1)

# 3) Task claim latency: remove the pre-claim SELECT. The DB unique constraint remains the guard.
old_claim = '''    try:\n        existing = (\n            client.table("player_task_claims")\n            .select("task_id")\n            .eq("user_key", user_key)\n            .eq("period_type", period_type)\n            .eq("period_key", period_key)\n            .eq("task_id", task["id"])\n            .limit(1)\n            .execute()\n        )\n        if existing.data:\n            return False, "這個任務獎勵已經領取過了。"\n\n        client.table("player_task_claims").insert({\n            "user_key": user_key,\n            "period_type": period_type,\n            "period_key": period_key,\n            "task_id": task["id"],\n            "reward_type": task["reward_type"],\n            "reward_amount": int(task["reward_amount"]),\n            "claimed_at": datetime.now(timezone.utc).isoformat(),\n        }).execute()\n    except Exception as error:\n        return False, f"Supabase 任務紀錄失敗：{type(error).__name__}"\n'''
new_claim = '''    try:\n        client.table("player_task_claims").insert({\n            "user_key": user_key,\n            "period_type": period_type,\n            "period_key": period_key,\n            "task_id": task["id"],\n            "reward_type": task["reward_type"],\n            "reward_amount": int(task["reward_amount"]),\n            "claimed_at": datetime.now(timezone.utc).isoformat(),\n        }).execute()\n    except Exception as error:\n        error_text = str(error).lower()\n        if "23505" in error_text or "duplicate" in error_text or "unique" in error_text:\n            return False, "這個任務獎勵已經領取過了。"\n        return False, f"Supabase 任務紀錄失敗：{type(error).__name__}"\n'''
if old_claim not in s:
    raise RuntimeError('task claim block not found')
s = s.replace(old_claim, new_claim, 1)

p.write_text(s, encoding='utf-8')
