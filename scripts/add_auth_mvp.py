from pathlib import Path
import re

p = Path('streamlit_app.py')
s = p.read_text(encoding='utf-8')

# ---------- defaults ----------
anchor = '    "slime_dev_preview": False,\n'
insert = '    "auth_user_id": None,\n    "auth_email": None,\n    "auth_mode": "login",\n'
if '"auth_user_id": None' not in s:
    if anchor not in s:
        raise RuntimeError('default state anchor not found')
    s = s.replace(anchor, insert + anchor, 1)

# ---------- auth helpers ----------
auth_anchor = '\ndef _achievement_supabase_client():\n'
if 'def _auth_client()' not in s:
    if auth_anchor not in s:
        raise RuntimeError('achievement client anchor not found')
    auth_code = r'''

def _auth_client():
    """Per-Streamlit-session Supabase client. Never cache this globally: auth state is user-specific."""
    client = st.session_state.get("_auth_client_obj")
    if client is not None:
        return client
    try:
        url = str(st.secrets["SUPABASE_URL"]).strip().replace("\ufeff", "").replace("\u200b", "")
        key = str(st.secrets["SUPABASE_KEY"]).strip().replace("\ufeff", "").replace("\u200b", "")
        client = create_client(url, key)
        st.session_state["_auth_client_obj"] = client
        return client
    except Exception:
        return None


def _auth_user_id():
    value = str(st.session_state.get("auth_user_id") or "").strip()
    return value or None


def _auth_user():
    user_id = _auth_user_id()
    if not user_id:
        return None
    return {"id": user_id, "email": st.session_state.get("auth_email")}


def _reset_user_scoped_state():
    """Prevent one account's Streamlit state from leaking into the next login in the same browser session."""
    user_keys = [
        "coins", "tickets", "streak", "selected_slime", "collection", "gacha_pity", "gacha_free_date",
        "gacha_pull_count", "focus_seconds_total", "focus_seconds_today", "focus_coins_today",
        "achievement_claimed", "achievement_unlocked_at", "slime_accessories", "slime_accessory_equipped",
        "slime_progress", "slime_nicknames", "game_state_fingerprint",
    ]
    for key in user_keys:
        default = DEFAULT_STATE.get(key)
        if isinstance(default, dict):
            st.session_state[key] = default.copy()
        elif isinstance(default, list):
            st.session_state[key] = default.copy()
        else:
            st.session_state[key] = default
    st.session_state.game_state_loaded = False
    st.session_state.game_state_db_ready = False
    st.session_state.game_state_error = None
    st.session_state.achievement_user_key = None
    st.session_state.medslime_page = "home"


def _set_authenticated_user(user):
    user_id = str(getattr(user, "id", "") or "").strip()
    if not user_id:
        raise ValueError("Supabase 沒有回傳使用者 ID。")
    _reset_user_scoped_state()
    st.session_state.auth_user_id = user_id
    st.session_state.auth_email = str(getattr(user, "email", "") or "").strip()
    st.session_state.achievement_user_key = user_id


def _sign_out():
    client = _auth_client()
    try:
        if client:
            client.auth.sign_out()
    except Exception:
        pass
    _reset_user_scoped_state()
    st.session_state.auth_user_id = None
    st.session_state.auth_email = None
    st.session_state.auth_mode = "login"
    st.session_state.pop("_auth_client_obj", None)


def auth_page():
    st.markdown(
        """
        <style>
        .auth-shell{max-width:480px;margin:5vh auto 0}.auth-brand{font-size:2rem;font-weight:950;color:#17372a!important;letter-spacing:-.04em}.auth-card{border:1px solid #dbe9e1;background:rgba(255,255,255,.96);border-radius:24px;padding:1.35rem 1.4rem;margin-top:1rem;box-shadow:0 14px 34px rgba(32,85,54,.08)}.auth-title{font-size:1.35rem;font-weight:950;color:#17372a!important}.auth-copy{color:#789083!important;margin:.25rem 0 .9rem}.auth-marker{display:none}[data-testid="stMainBlockContainer"]:has(.auth-marker) p,[data-testid="stMainBlockContainer"]:has(.auth-marker) label{color:#244c39!important}
        </style>
        <div class="auth-marker"></div><div class="auth-shell"><div class="auth-brand">MedSlime.</div></div>
        """,
        unsafe_allow_html=True,
    )
    mode = st.radio("帳號", ["登入", "註冊", "忘記密碼"], horizontal=True, label_visibility="collapsed", key="auth_mode_radio")
    client = _auth_client()
    if not client:
        st.error("目前無法連線 Supabase Auth。")
        return

    with st.container(key="auth_form_card"):
        if mode == "登入":
            st.markdown('<div class="auth-title">登入</div><div class="auth-copy">使用 Email + Password。</div>', unsafe_allow_html=True)
            email = st.text_input("Email", key="auth_login_email")
            password = st.text_input("密碼", type="password", key="auth_login_password")
            if st.button("登入", type="primary", use_container_width=True, key="auth_login_submit"):
                try:
                    response = client.auth.sign_in_with_password({"email": email.strip(), "password": password})
                    if not response.user:
                        raise ValueError("登入失敗")
                    _set_authenticated_user(response.user)
                    st.rerun()
                except Exception as error:
                    st.error("登入失敗，請確認 Email 與密碼。")
                    st.caption(f"{type(error).__name__}: {error}")
        elif mode == "註冊":
            st.markdown('<div class="auth-title">建立帳號</div><div class="auth-copy">MVP 先只支援 Email + Password。</div>', unsafe_allow_html=True)
            email = st.text_input("Email", key="auth_signup_email")
            password = st.text_input("密碼", type="password", key="auth_signup_password")
            password2 = st.text_input("再次輸入密碼", type="password", key="auth_signup_password2")
            if st.button("註冊", type="primary", use_container_width=True, key="auth_signup_submit"):
                if len(password) < 6:
                    st.warning("密碼至少 6 個字元。")
                elif password != password2:
                    st.warning("兩次密碼不一致。")
                else:
                    try:
                        response = client.auth.sign_up({"email": email.strip(), "password": password})
                        if response.session and response.user:
                            _set_authenticated_user(response.user)
                            st.rerun()
                        else:
                            st.success("註冊成功。請先到信箱完成 Email 驗證，再回來登入。")
                    except Exception as error:
                        st.error("註冊失敗。")
                        st.caption(f"{type(error).__name__}: {error}")
        else:
            st.markdown('<div class="auth-title">忘記密碼</div><div class="auth-copy">輸入註冊 Email，Supabase 會寄出重設密碼信。</div>', unsafe_allow_html=True)
            email = st.text_input("Email", key="auth_reset_email")
            if st.button("寄送重設密碼信", type="primary", use_container_width=True, key="auth_reset_submit"):
                try:
                    client.auth.reset_password_email(email.strip())
                    st.success("如果這個 Email 已註冊，重設密碼信已寄出。")
                except Exception as error:
                    st.error("目前無法寄送重設密碼信。")
                    st.caption(f"{type(error).__name__}: {error}")
'''
    s = s.replace(auth_anchor, auth_code + auth_anchor, 1)

# Replace private-data client helper with authenticated session client.
pattern = r'def _achievement_supabase_client\(\):\n.*?\n\ndef _prototype_user_key\(\):'
m = re.search(pattern, s, flags=re.S)
if not m:
    raise RuntimeError('private client/prototype key block not found')
replacement = '''def _achievement_supabase_client():\n    return _auth_client() if _auth_user_id() else None\n\n\ndef _prototype_user_key():\n    """Legacy compatibility name. Private data is now keyed by auth.users.id."""\n    return _auth_user_id()\n'''
# Keep the original prototype body out by replacing through the next function.
start = m.start()
proto_start = s.index('def _prototype_user_key():', m.start())
proto_end = s.index('\ndef _game_state_snapshot():', proto_start)
s = s[:start] + replacement + s[proto_end:]

# achievement user key = auth uid
ach_start = s.index('def _achievement_user_key():')
ach_end = s.index('\ndef _achievement_progress(', ach_start)
s = s[:ach_start] + '''def _achievement_user_key():\n    return _auth_user_id()\n\n''' + s[ach_end+1:]

# ---------- mistake bank isolation ----------
old = '''def load_mistake_bank():\n    response = (\n        get_supabase()\n        .table("mistakes")\n        .select("*")\n        .order("created_at", desc=True)\n        .execute()\n    )\n    return response.data or []\n'''
new = '''def load_mistake_bank():\n    client = _achievement_supabase_client()\n    if not client or not _auth_user_id():\n        return []\n    response = (\n        client.table("mistakes")\n        .select("*")\n        .eq("user_id", _auth_user_id())\n        .order("created_at", desc=True)\n        .execute()\n    )\n    return response.data or []\n'''
if old not in s:
    raise RuntimeError('load_mistake_bank anchor missing')
s = s.replace(old, new, 1)

old = '''    (\n        get_supabase()\n        .table("mistakes")\n        .update({"label": f"{_REVIEWED_PREFIX}{reviewed_at}"})\n        .eq("id", record_id)\n        .execute()\n    )\n'''
new = '''    client = _achievement_supabase_client()\n    if not client or not _auth_user_id():\n        raise RuntimeError("尚未登入")\n    (\n        client.table("mistakes")\n        .update({"label": f"{_REVIEWED_PREFIX}{reviewed_at}"})\n        .eq("id", record_id)\n        .eq("user_id", _auth_user_id())\n        .execute()\n    )\n'''
if old not in s:
    raise RuntimeError('mark mistake anchor missing')
s = s.replace(old, new, 1)

# Add user_id to each mistake row and authenticated insert.
row_anchor = '        rows.append({\n            "subject": subject,\n'
if row_anchor not in s:
    raise RuntimeError('mistake row anchor missing')
s = s.replace(row_anchor, '        rows.append({\n            "user_id": _auth_user_id(),\n            "subject": subject,\n', 1)
s = s.replace('        get_supabase().table("mistakes").insert(rows).execute()\n', '        client = _achievement_supabase_client()\n        if not client:\n            raise RuntimeError("尚未登入")\n        client.table("mistakes").insert(rows).execute()\n', 1)

# ---------- add user_id to private-table writes ----------
replacements = [
    ('{"user_key": user_key, **snapshot["player"], "updated_at": now_iso}', '{"user_key": user_key, "user_id": _auth_user_id(), **snapshot["player"], "updated_at": now_iso}'),
    ('{"user_key": user_key, **row, "updated_at": now_iso}', '{"user_key": user_key, "user_id": _auth_user_id(), **row, "updated_at": now_iso}'),
    ('"user_key": _achievement_user_key(),\n                "achievement_id": aid,', '"user_key": _achievement_user_key(),\n                "user_id": _auth_user_id(),\n                "achievement_id": aid,'),
    ('"user_key": user_key,\n                "event_date": day_key,', '"user_key": user_key,\n                "user_id": _auth_user_id(),\n                "event_date": day_key,'),
    ('"user_key": user_key,\n            "event_date": day_key,', '"user_key": user_key,\n            "user_id": _auth_user_id(),\n            "event_date": day_key,'),
    ('"user_key": user_key,\n            "quiz_token": quiz_token,', '"user_key": user_key,\n            "user_id": _auth_user_id(),\n            "quiz_token": quiz_token,'),
    ('"user_key": user_key,\n            "period_type": period_type,', '"user_key": user_key,\n            "user_id": _auth_user_id(),\n            "period_type": period_type,'),
    ('"user_key": _prototype_user_key(),\n            "session_token": token,', '"user_key": _prototype_user_key(),\n            "user_id": _auth_user_id(),\n            "session_token": token,'),
]
for old_text, new_text in replacements:
    if old_text in s:
        s = s.replace(old_text, new_text)

# ---------- topbar logout ----------
topbar_start = s.index('def topbar():')
topbar_end = s.index('\ndef slime_markup():', topbar_start)
old_topbar = s[topbar_start:topbar_end]
new_topbar = '''def topbar():\n    with st.container(key="topbar_shell"):\n        brand_col, currency_col, auth_col = st.columns([1, 2.1, .45], vertical_alignment="center")\n        with brand_col:\n            if st.button("MedSlime.", key=f"brand_home_{st.session_state.medslime_page}", help="返回首頁"):\n                goto("home")\n        with currency_col:\n            st.markdown(\n                f'<div class="currency"><span class="pill">🔥 {st.session_state.streak} 天</span><span class="pill">🪙 {st.session_state.coins}</span><span class="pill">🎫 {st.session_state.tickets}</span></div>',\n                unsafe_allow_html=True,\n            )\n        with auth_col:\n            if st.button("登出", key=f"logout_{st.session_state.medslime_page}", use_container_width=True):\n                _sign_out()\n                st.rerun()\n\n'''
s = s[:topbar_start] + new_topbar + s[topbar_end+1:]

# ---------- auth gate before all private app loading ----------
old_dispatch = '''# Load persistent player/slime state before rendering pages.\n_load_game_state_from_supabase_once()\n_task_mark_active_day()\nrender_quick_scroll_nav()\n'''
new_dispatch = '''# Authentication gate: private data is never loaded before Supabase Auth succeeds.\nif not _auth_user():\n    auth_page()\n    st.stop()\n\n# Load persistent player/slime state only for the authenticated auth.users.id.\n_load_game_state_from_supabase_once()\n_task_mark_active_day()\nrender_quick_scroll_nav()\n'''
if old_dispatch not in s:
    raise RuntimeError('dispatcher auth gate anchor missing')
s = s.replace(old_dispatch, new_dispatch, 1)

p.write_text(s, encoding='utf-8')
