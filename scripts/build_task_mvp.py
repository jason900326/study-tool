from pathlib import Path
import re

p = Path('streamlit_app.py')
s = p.read_text(encoding='utf-8')

# ---------------------------------------------------------------------------
# Imports / definitions
# ---------------------------------------------------------------------------
s = s.replace(
    'from datetime import datetime, timezone\n',
    'from datetime import datetime, timezone, timedelta\n',
    1,
)

if 'DAILY_TASKS = [' not in s:
    anchor = '\n\nSLIME_CATALOG = ['
    idx = s.index(anchor)
    task_defs = '''

DAILY_TASKS = [
    {"id":"daily_answer_5","icon":"🧠","title":"完成 5 題","metric":"answered","target":5,"reward_type":"coins","reward_amount":10},
    {"id":"daily_review_1","icon":"🔍","title":"訂正 1 題","metric":"reviewed","target":1,"reward_type":"coins","reward_amount":10},
    {"id":"daily_focus_20","icon":"⏱️","title":"專注 20 分鐘","metric":"focus_minutes","target":20,"reward_type":"coins","reward_amount":10},
]

WEEKLY_TASKS = [
    {"id":"weekly_days_5","icon":"📅","title":"本週使用 5 天","metric":"active_days","target":5},
    {"id":"weekly_answer_200","icon":"🧠","title":"本週完成 200 題","metric":"answered","target":200},
    {"id":"weekly_review_20","icon":"🔍","title":"本週訂正 20 題","metric":"reviewed","target":20},
    {"id":"weekly_focus_180","icon":"⏱️","title":"本週專注 180 分鐘","metric":"focus_minutes","target":180},
]

WEEKLY_ALL_REWARD = {"id":"weekly_all","icon":"🎁","title":"完成全部週任務","reward_type":"tickets","reward_amount":1}
'''
    s = s[:idx] + task_defs + s[idx:]

# ---------------------------------------------------------------------------
# Task storage / calculations / page
# Insert before achievements_page so all helpers exist by render time.
# ---------------------------------------------------------------------------
if 'def _task_today():' not in s:
    insert_at = s.index('\ndef achievements_page():')
    task_helpers = r'''

# =========================================================
# Daily / weekly task MVP
# =========================================================

_TASK_TZ = timezone(timedelta(hours=8))


def _task_today():
    return datetime.now(_TASK_TZ).date()


def _task_day_key(day=None):
    return (day or _task_today()).isoformat()


def _task_week_bounds(day=None):
    day = day or _task_today()
    start = day - timedelta(days=day.weekday())
    end = start + timedelta(days=6)
    return start, end


def _task_week_key(day=None):
    start, _ = _task_week_bounds(day)
    return start.isoformat()


def _task_client():
    return _achievement_supabase_client()


def _task_mark_active_day():
    client = _task_client()
    if not client:
        return False
    user_key = _prototype_user_key()
    day_key = _task_day_key()
    try:
        existing = (
            client.table("player_task_events")
            .select("event_date")
            .eq("user_key", user_key)
            .eq("event_date", day_key)
            .limit(1)
            .execute()
        )
        if not (existing.data or []):
            client.table("player_task_events").insert({
                "user_key": user_key,
                "event_date": day_key,
                "answered_count": 0,
                "reviewed_count": 0,
                "focus_seconds": 0,
            }).execute()
        return True
    except Exception:
        return False


def _task_record_event(answered=0, reviewed=0, focus_seconds=0):
    answered = max(0, int(answered or 0))
    reviewed = max(0, int(reviewed or 0))
    focus_seconds = max(0, int(focus_seconds or 0))
    if not (answered or reviewed or focus_seconds):
        return True
    client = _task_client()
    if not client:
        return False
    user_key = _prototype_user_key()
    day_key = _task_day_key()
    try:
        response = (
            client.table("player_task_events")
            .select("answered_count,reviewed_count,focus_seconds")
            .eq("user_key", user_key)
            .eq("event_date", day_key)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        row = rows[0] if rows else {}
        payload = {
            "user_key": user_key,
            "event_date": day_key,
            "answered_count": int(row.get("answered_count", 0) or 0) + answered,
            "reviewed_count": int(row.get("reviewed_count", 0) or 0) + reviewed,
            "focus_seconds": int(row.get("focus_seconds", 0) or 0) + focus_seconds,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        client.table("player_task_events").upsert(
            payload,
            on_conflict="user_key,event_date",
        ).execute()
        return True
    except Exception:
        return False


def _task_record_quiz_once(kind, token, answered_count):
    answered_count = max(0, int(answered_count or 0))
    if answered_count <= 0:
        return False
    token = str(token or "").strip()
    if not token:
        return False
    client = _task_client()
    if not client:
        return False
    user_key = _prototype_user_key()
    quiz_token = hashlib.sha256(f"{kind}|{token}".encode("utf-8")).hexdigest()[:48]
    try:
        existing = (
            client.table("player_task_quiz_events")
            .select("quiz_token")
            .eq("user_key", user_key)
            .eq("quiz_token", quiz_token)
            .limit(1)
            .execute()
        )
        if existing.data:
            return False
        client.table("player_task_quiz_events").insert({
            "user_key": user_key,
            "quiz_token": quiz_token,
            "answered_count": answered_count,
        }).execute()
        _task_record_event(answered=answered_count)
        return True
    except Exception:
        return False


def _task_event_rows(start_day, end_day):
    client = _task_client()
    if not client:
        return []
    try:
        response = (
            client.table("player_task_events")
            .select("event_date,answered_count,reviewed_count,focus_seconds")
            .eq("user_key", _prototype_user_key())
            .gte("event_date", start_day.isoformat())
            .lte("event_date", end_day.isoformat())
            .execute()
        )
        return response.data or []
    except Exception:
        return []


def _task_claim_rows(period_type, period_key):
    client = _task_client()
    if not client:
        return []
    try:
        response = (
            client.table("player_task_claims")
            .select("task_id,reward_type,reward_amount,claimed_at")
            .eq("user_key", _prototype_user_key())
            .eq("period_type", period_type)
            .eq("period_key", period_key)
            .execute()
        )
        return response.data or []
    except Exception:
        return []


def _task_daily_snapshot():
    day = _task_today()
    rows = _task_event_rows(day, day)
    row = rows[0] if rows else {}
    return {
        "answered": int(row.get("answered_count", 0) or 0),
        "reviewed": int(row.get("reviewed_count", 0) or 0),
        "focus_minutes": int(row.get("focus_seconds", 0) or 0) // 60,
    }


def _task_weekly_snapshot():
    start, end = _task_week_bounds()
    rows = _task_event_rows(start, end)
    return {
        "active_days": len({str(row.get("event_date")) for row in rows if row.get("event_date")}),
        "answered": sum(int(row.get("answered_count", 0) or 0) for row in rows),
        "reviewed": sum(int(row.get("reviewed_count", 0) or 0) for row in rows),
        "focus_minutes": sum(int(row.get("focus_seconds", 0) or 0) for row in rows) // 60,
    }


def _task_progress_text(task, value):
    metric = task["metric"]
    target = int(task["target"])
    if metric == "active_days":
        return f"{min(int(value), target)} / {target} 天"
    if metric == "focus_minutes":
        return f"{min(int(value), target)} / {target} 分鐘"
    if metric == "answered":
        return f"{min(int(value), target)} / {target} 題"
    if metric == "reviewed":
        return f"{min(int(value), target)} / {target} 題"
    return f"{min(int(value), target)} / {target}"


def _task_reward_text(task):
    if task.get("reward_type") == "coins":
        return f"🪙 {int(task.get('reward_amount', 0))}"
    if task.get("reward_type") == "tickets":
        return f"🎫 {int(task.get('reward_amount', 0))}"
    return ""


def _task_claim(task, period_type, period_key, progress_value, completed_override=None):
    target = int(task.get("target", 1) or 1)
    completed = bool(completed_override) if completed_override is not None else int(progress_value) >= target
    if not completed or not task.get("reward_type"):
        return False, "目前不能領取這個獎勵。"

    client = _task_client()
    if not client:
        return False, "Supabase 任務表尚未連上。"
    user_key = _prototype_user_key()
    try:
        existing = (
            client.table("player_task_claims")
            .select("task_id")
            .eq("user_key", user_key)
            .eq("period_type", period_type)
            .eq("period_key", period_key)
            .eq("task_id", task["id"])
            .limit(1)
            .execute()
        )
        if existing.data:
            return False, "這個任務獎勵已經領取過了。"

        client.table("player_task_claims").insert({
            "user_key": user_key,
            "period_type": period_type,
            "period_key": period_key,
            "task_id": task["id"],
            "reward_type": task["reward_type"],
            "reward_amount": int(task["reward_amount"]),
            "claimed_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as error:
        return False, f"Supabase 任務紀錄失敗：{type(error).__name__}"

    if task["reward_type"] == "coins":
        st.session_state.coins += int(task["reward_amount"])
    else:
        st.session_state.tickets += int(task["reward_amount"])
    try:
        _save_game_state_to_supabase_if_changed()
    except Exception:
        pass
    return True, f"已領取 {_task_reward_text(task)}"


def _render_task_card(task, value, completed, claimed, period_type, period_key, key_prefix, allow_claim=True):
    target = int(task.get("target", 1) or 1)
    pct = max(0, min(100, round((float(value) / target) * 100))) if target else 100
    status = "✓ 已領取" if claimed else ("✓ 已完成" if completed else "進行中")
    status_class = "claimed" if claimed else ("done" if completed else "pending")
    reward = _task_reward_text(task)
    reward_html = f'<span class="task-mvp-reward">獎勵 {html.escape(reward)}</span>' if reward else '<span></span>'
    st.markdown(
        f'<div class="task-mvp-card"><div class="task-mvp-top"><div><div class="task-mvp-name">{task.get("icon", "")} {html.escape(task["title"])}</div>'
        f'<div class="task-mvp-progressline"><span>{html.escape(_task_progress_text(task, value))}</span>{reward_html}</div></div>'
        f'<div class="task-mvp-status {status_class}">{status}</div></div>'
        f'<div class="task-mvp-track"><div class="task-mvp-fill" style="width:{pct}%"></div></div></div>',
        unsafe_allow_html=True,
    )
    if allow_claim and task.get("reward_type"):
        label = "已領取" if claimed else ("領取獎勵" if completed else "尚未完成")
        if st.button(label, key=f"{key_prefix}_{task['id']}", disabled=claimed or not completed, use_container_width=True, type="primary" if completed and not claimed else "secondary"):
            ok, message = _task_claim(task, period_type, period_key, value)
            if ok:
                st.toast(message, icon="🎁")
                st.rerun()
            else:
                st.warning(message)


def tasks_page():
    topbar()
    render_back_button("返回首頁", "home", "back_tasks")
    st.markdown(
        """
        <style>
        .task-mvp-marker{display:none}.task-mvp-title{font-size:2rem;font-weight:950;color:#17372a!important;letter-spacing:-.04em}.task-mvp-sub{color:#789083!important;margin:.25rem 0 1rem}.task-mvp-card{border:1px solid #dbe9e1;background:rgba(255,255,255,.95);border-radius:20px;padding:1rem 1.05rem;margin:.6rem 0 .25rem;box-shadow:0 8px 22px rgba(32,85,54,.05)}.task-mvp-top{display:flex;justify-content:space-between;gap:.8rem;align-items:flex-start}.task-mvp-name{font-weight:950;color:#17372a!important}.task-mvp-progressline{display:flex;gap:1rem;margin-top:.28rem;color:#6f887b!important;font-size:.78rem}.task-mvp-reward{font-weight:900;color:#315b45!important}.task-mvp-status{white-space:nowrap;padding:.25rem .55rem;border-radius:999px;font-size:.68rem;font-weight:900}.task-mvp-status.pending{background:#f1f4f2;color:#789083}.task-mvp-status.done{background:#e9f8ef;color:#28754b}.task-mvp-status.claimed{background:#edf4ef;color:#557768}.task-mvp-track{height:7px;background:#e6eee9;border-radius:999px;overflow:hidden;margin-top:.65rem}.task-mvp-fill{height:100%;background:#55b97b;border-radius:999px}[data-testid="stMainBlockContainer"]:has(.task-mvp-marker) h1,[data-testid="stMainBlockContainer"]:has(.task-mvp-marker) h2,[data-testid="stMainBlockContainer"]:has(.task-mvp-marker) h3,[data-testid="stMainBlockContainer"]:has(.task-mvp-marker) p,[data-testid="stMainBlockContainer"]:has(.task-mvp-marker) label{color:#244c39!important}@media(max-width:767px){.task-mvp-title{font-size:1.7rem}.task-mvp-card{padding:.85rem}.task-mvp-progressline{flex-direction:column;gap:.1rem}.task-mvp-status{font-size:.62rem}}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="task-mvp-marker"></div>', unsafe_allow_html=True)
    st.markdown('<div class="task-mvp-title">📋 任務</div><div class="task-mvp-sub">每日任務每天重置；週任務以週一到週日計算。</div>', unsafe_allow_html=True)

    if not _task_mark_active_day():
        st.caption("Supabase 任務表尚未建立時，任務進度不會正式保存。請先執行 supabase/task_mvp.sql。")

    daily = _task_daily_snapshot()
    daily_key = _task_day_key()
    daily_claims = {row.get("task_id") for row in _task_claim_rows("daily", daily_key)}
    st.markdown("### 今日任務")
    for task in DAILY_TASKS:
        value = daily.get(task["metric"], 0)
        completed = value >= task["target"]
        _render_task_card(task, value, completed, task["id"] in daily_claims, "daily", daily_key, "claim_daily")

    weekly = _task_weekly_snapshot()
    weekly_key = _task_week_key()
    weekly_claims = {row.get("task_id") for row in _task_claim_rows("weekly", weekly_key)}
    st.markdown("### 本週任務")
    completed_weekly = 0
    for task in WEEKLY_TASKS:
        value = weekly.get(task["metric"], 0)
        completed = value >= task["target"]
        completed_weekly += int(completed)
        _render_task_card(task, value, completed, False, "weekly", weekly_key, "weekly_progress", allow_claim=False)

    all_done = completed_weekly == len(WEEKLY_TASKS)
    all_task = {**WEEKLY_ALL_REWARD, "metric":"weekly_all", "target":len(WEEKLY_TASKS)}
    _render_task_card(
        all_task,
        completed_weekly,
        all_done,
        WEEKLY_ALL_REWARD["id"] in weekly_claims,
        "weekly",
        weekly_key,
        "claim_weekly_all",
        allow_claim=True,
    )
'''
    s = s[:insert_at] + task_helpers + s[insert_at:]

# ---------------------------------------------------------------------------
# Home: replace legacy fake task cards with real daily summary + entry button.
# ---------------------------------------------------------------------------
home_pattern = re.compile(
    r'    st\.markdown\(\'<div class="section-title">今日任務</div>\'.*?\n\n\ndef study_home\(\):',
    re.S,
)
home_replacement = '''    st.markdown('<div class="section-title">今日任務</div>', unsafe_allow_html=True)
    _task_mark_active_day()
    daily = _task_daily_snapshot()
    cols = st.columns(3, gap="medium")
    for col, task in zip(cols, DAILY_TASKS):
        value = daily.get(task["metric"], 0)
        progress = _task_progress_text(task, value)
        reward = _task_reward_text(task)
        done = value >= task["target"]
        with col:
            st.markdown(
                f'<div class="home-task"><div class="task-icon">{task["icon"]}</div><div class="card-title">{html.escape(task["title"])}</div>'
                f'<div class="muted">{html.escape(progress)}</div><div class="task-reward">{"✓ 已完成" if done else html.escape(reward)}</div></div>',
                unsafe_allow_html=True,
            )
    if st.button("查看每日／每週任務", use_container_width=True, key="home_open_tasks"):
        goto("tasks")


def study_home():'''
s, home_count = home_pattern.subn(home_replacement, s, count=1)
if home_count != 1:
    raise RuntimeError(f'home task block patch count={home_count}')

# ---------------------------------------------------------------------------
# Count quiz answers exactly once per attempt.
# ---------------------------------------------------------------------------
material_anchor = '''def material_quiz_result():
    questions = st.session_state.material_questions or []
    if len(questions) != QUIZ_SIZE:
        goto("study_material_intro")

    topbar()
'''
material_new = '''def material_quiz_result():
    questions = st.session_state.material_questions or []
    if len(questions) != QUIZ_SIZE:
        goto("study_material_intro")

    material_task_token = f"{st.session_state.get('material_file_hash')}|{st.session_state.get('material_quiz_started_at')}"
    _task_record_quiz_once("material", material_task_token, len(st.session_state.get("quiz_answers", {})))
    topbar()
'''
if material_anchor not in s:
    raise RuntimeError('material result anchor not found')
s = s.replace(material_anchor, material_new, 1)

national_anchor = '''def national_exam_result_page():
    questions = st.session_state.national_exam_questions or []
    if not questions:
        goto("national_exam")
    topbar()
'''
national_new = '''def national_exam_result_page():
    questions = st.session_state.national_exam_questions or []
    if not questions:
        goto("national_exam")
    national_task_token = f"{st.session_state.get('national_exam_started_at')}|{st.session_state.get('national_exam_meta')}"
    _task_record_quiz_once("national", national_task_token, len(st.session_state.get("national_exam_answers", {})))
    topbar()
'''
if national_anchor not in s:
    raise RuntimeError('national result anchor not found')
s = s.replace(national_anchor, national_new, 1)

# ---------------------------------------------------------------------------
# Count mistake reviews after DB update.
# ---------------------------------------------------------------------------
review_anchor = '''def mark_mistake_reviewed(record_id):
    reviewed_at = datetime.now(timezone.utc).isoformat()
    (
        get_supabase()
        .table("mistakes")
        .update({"label": f"{_REVIEWED_PREFIX}{reviewed_at}"})
        .eq("id", record_id)
        .execute()
    )
'''
review_new = review_anchor + '    _task_record_event(reviewed=1)\n'
if review_anchor not in s:
    raise RuntimeError('mark_mistake_reviewed anchor not found')
s = s.replace(review_anchor, review_new, 1)

# ---------------------------------------------------------------------------
# Count focused seconds in the same two places focus totals are awarded.
# ---------------------------------------------------------------------------
focus_stop_old = '''        st.session_state.focus_seconds_today += elapsed
        st.session_state.focus_seconds_total += elapsed
'''
focus_stop_new = focus_stop_old + '        _task_record_event(focus_seconds=elapsed)\n'
if focus_stop_old not in s:
    raise RuntimeError('focus stop anchor not found')
s = s.replace(focus_stop_old, focus_stop_new, 1)

focus_done_old = '''            st.session_state.focus_seconds_today += st.session_state.focus_total_seconds
            st.session_state.focus_seconds_total += st.session_state.focus_total_seconds
'''
focus_done_new = focus_done_old + '            _task_record_event(focus_seconds=st.session_state.focus_total_seconds)\n'
if focus_done_old not in s:
    raise RuntimeError('focus completion anchor not found')
s = s.replace(focus_done_old, focus_done_new, 1)

# ---------------------------------------------------------------------------
# Mark today active after persistent game state is loaded.
# ---------------------------------------------------------------------------
load_anchor = '''# Load persistent player/slime state before rendering pages.
_load_game_state_from_supabase_once()
render_quick_scroll_nav()
'''
load_new = '''# Load persistent player/slime state before rendering pages.
_load_game_state_from_supabase_once()
_task_mark_active_day()
render_quick_scroll_nav()
'''
if load_anchor not in s:
    raise RuntimeError('bottom load anchor not found')
s = s.replace(load_anchor, load_new, 1)

# Route tasks page.
route_anchor = '''elif page == "achievements":
    achievements_page()
else:
'''
route_new = '''elif page == "achievements":
    achievements_page()
elif page == "tasks":
    tasks_page()
else:
'''
if route_anchor not in s:
    raise RuntimeError('route anchor not found')
s = s.replace(route_anchor, route_new, 1)

p.write_text(s, encoding='utf-8')
print('Built daily/weekly task MVP')
