from pathlib import Path

p = Path('streamlit_app.py')
s = p.read_text(encoding='utf-8')

# 1) Add persistent-game bookkeeping to session defaults.
if '"game_state_loaded": False' not in s:
    anchor = '    "achievement_user_key": None,\n'
    if anchor not in s:
        raise RuntimeError('achievement_user_key state anchor not found')
    addition = (
        anchor
        + '    "game_state_loaded": False,\n'
        + '    "game_state_db_ready": False,\n'
        + '    "game_state_error": None,\n'
        + '    "game_state_fingerprint": None,\n'
        + '    "slime_accessories": {},\n'
    )
    s = s.replace(anchor, addition, 1)

# 2) Insert reusable persistence helpers after the Supabase client helper.
if 'def _load_game_state_from_supabase_once():' not in s:
    anchor = '\n\ndef _achievement_user_key():\n'
    if anchor not in s:
        raise RuntimeError('achievement helper anchor not found')
    helpers = r'''

def _prototype_user_key():
    """Stable per-browser-link key for the MVP until real authentication exists."""
    try:
        query_value = st.query_params.get("player")
        if isinstance(query_value, (list, tuple)):
            query_value = query_value[0] if query_value else None
        query_value = str(query_value or "").strip()
    except Exception:
        query_value = ""

    existing = str(st.session_state.get("achievement_user_key") or "").strip()
    key = query_value or existing
    if not key:
        seed = f"{time.time_ns()}-{random.random()}-{st.session_state.get('slime_name','Medi')}"
        key = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24]

    st.session_state.achievement_user_key = key
    if not query_value:
        try:
            st.query_params["player"] = key
        except Exception:
            pass
    return key


def _game_state_snapshot():
    collection = [name for name in st.session_state.get("collection", []) if name in SLIME_BY_NAME]
    if "綠色史萊姆" not in collection:
        collection.insert(0, "綠色史萊姆")

    selected = st.session_state.get("selected_slime")
    if selected not in collection:
        selected = "綠色史萊姆"

    player = {
        "coins": max(0, int(st.session_state.get("coins", 0) or 0)),
        "tickets": max(0, int(st.session_state.get("tickets", 0) or 0)),
        "streak": max(0, int(st.session_state.get("streak", 0) or 0)),
        "selected_slime": selected,
        "gacha_pity": max(0, int(st.session_state.get("gacha_pity", 0) or 0)),
        "gacha_free_date": st.session_state.get("gacha_free_date") or None,
        "gacha_pull_count": max(0, int(st.session_state.get("gacha_pull_count", 0) or 0)),
        "focus_seconds_total": max(0, int(st.session_state.get("focus_seconds_total", 0) or 0)),
        "focus_seconds_today": max(0, int(st.session_state.get("focus_seconds_today", 0) or 0)),
        "focus_coins_today": max(0, int(st.session_state.get("focus_coins_today", 0) or 0)),
    }

    accessories = st.session_state.setdefault("slime_accessories", {})
    nicknames = st.session_state.setdefault("slime_nicknames", {})
    slimes = []
    for item in SLIME_CATALOG:
        name = item["name"]
        progress = get_slime_progress(name)
        owned = name in collection
        nickname = str(nicknames.get(name) or "").strip() or (get_slime_nickname(name) if owned else None)
        slimes.append(
            {
                "slime_name": name,
                "owned": owned,
                "fragments": max(0, int(progress.get("fragments", 0) or 0)),
                "accessory_unlocked": bool(accessories.get(name, False)),
                "nickname": nickname,
                "acquired_order": collection.index(name) if owned else None,
            }
        )
    return {"player": player, "slimes": slimes}


def _game_state_fingerprint(snapshot=None):
    snapshot = snapshot or _game_state_snapshot()
    return hashlib.sha256(
        json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _save_game_state_to_supabase(force=False):
    if not st.session_state.get("game_state_loaded"):
        return False

    snapshot = _game_state_snapshot()
    fingerprint = _game_state_fingerprint(snapshot)
    if not force and fingerprint == st.session_state.get("game_state_fingerprint"):
        return True

    client = _achievement_supabase_client()
    if not client:
        st.session_state.game_state_db_ready = False
        st.session_state.game_state_error = "Supabase client unavailable"
        return False

    user_key = _prototype_user_key()
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        player_row = {"user_key": user_key, **snapshot["player"], "updated_at": now_iso}
        client.table("player_game_state").upsert(player_row, on_conflict="user_key").execute()

        slime_rows = []
        for row in snapshot["slimes"]:
            slime_row = {"user_key": user_key, **row, "updated_at": now_iso}
            if row["owned"]:
                # Preserve the first acquisition timestamp. We only set acquired_at on insert-like rows;
                # acquired_order remains the reliable ordering field for the current MVP.
                slime_row["acquired_at"] = now_iso
            slime_rows.append(slime_row)
        client.table("player_slimes").upsert(slime_rows, on_conflict="user_key,slime_name").execute()

        st.session_state.game_state_db_ready = True
        st.session_state.game_state_error = None
        st.session_state.game_state_fingerprint = fingerprint
        return True
    except Exception as error:
        st.session_state.game_state_db_ready = False
        st.session_state.game_state_error = f"{type(error).__name__}: {error}"
        return False


def _load_game_state_from_supabase_once():
    if st.session_state.get("game_state_loaded"):
        return bool(st.session_state.get("game_state_db_ready"))

    user_key = _prototype_user_key()
    client = _achievement_supabase_client()
    if not client:
        st.session_state.game_state_loaded = True
        st.session_state.game_state_db_ready = False
        st.session_state.game_state_error = "Supabase client unavailable"
        return False

    try:
        state_response = (
            client.table("player_game_state")
            .select("coins,tickets,streak,selected_slime,gacha_pity,gacha_free_date,gacha_pull_count,focus_seconds_total,focus_seconds_today,focus_coins_today")
            .eq("user_key", user_key)
            .limit(1)
            .execute()
        )
        slime_response = (
            client.table("player_slimes")
            .select("slime_name,owned,fragments,accessory_unlocked,nickname,acquired_order")
            .eq("user_key", user_key)
            .execute()
        )

        state_rows = state_response.data or []
        slime_rows = slime_response.data or []

        if state_rows:
            row = state_rows[0]
            for key in ("coins", "tickets", "streak", "gacha_pity", "gacha_pull_count", "focus_seconds_total", "focus_seconds_today", "focus_coins_today"):
                if row.get(key) is not None:
                    st.session_state[key] = int(row[key])
            st.session_state.gacha_free_date = row.get("gacha_free_date") or None
            if row.get("selected_slime") in SLIME_BY_NAME:
                st.session_state.selected_slime = row["selected_slime"]

        if slime_rows:
            valid_rows = [row for row in slime_rows if row.get("slime_name") in SLIME_BY_NAME]
            owned_rows = [row for row in valid_rows if row.get("owned")]
            owned_rows.sort(
                key=lambda row: (
                    row.get("acquired_order") is None,
                    int(row.get("acquired_order") or 0),
                    row.get("slime_name") or "",
                )
            )
            collection = [row["slime_name"] for row in owned_rows]
            if "綠色史萊姆" not in collection:
                collection.insert(0, "綠色史萊姆")
            st.session_state.collection = collection

            accessories = st.session_state.setdefault("slime_accessories", {})
            nicknames = st.session_state.setdefault("slime_nicknames", {})
            for slime_row in valid_rows:
                name = slime_row["slime_name"]
                get_slime_progress(name)["fragments"] = max(0, int(slime_row.get("fragments", 0) or 0))
                accessories[name] = bool(slime_row.get("accessory_unlocked", False))
                nickname = str(slime_row.get("nickname") or "").strip()
                if nickname:
                    nicknames[name] = nickname

        if st.session_state.get("selected_slime") not in st.session_state.get("collection", []):
            st.session_state.selected_slime = "綠色史萊姆"

        st.session_state.game_state_loaded = True
        st.session_state.game_state_db_ready = True
        st.session_state.game_state_error = None

        if not state_rows:
            # First visit for this prototype player: seed the database from the current session.
            _save_game_state_to_supabase(force=True)
        else:
            st.session_state.game_state_fingerprint = _game_state_fingerprint()
        return True
    except Exception as error:
        st.session_state.game_state_loaded = True
        st.session_state.game_state_db_ready = False
        st.session_state.game_state_error = f"{type(error).__name__}: {error}"
        return False


def _save_game_state_to_supabase_if_changed():
    if st.session_state.get("game_state_loaded"):
        _save_game_state_to_supabase(force=False)
'''
    s = s.replace(anchor, helpers + anchor, 1)

# 3) Persist achievement rewards into the same resource state.
if '# Persist the resource reward with the rest of the player game state.' not in s:
    anchor = '    st.session_state.achievement_claimed[aid] = claimed_at\n    return True, f"已領取 {_achievement_reward_text(item)}"\n'
    if anchor not in s:
        raise RuntimeError('achievement claim completion anchor not found')
    replacement = (
        '    st.session_state.achievement_claimed[aid] = claimed_at\n'
        '    # Persist the resource reward with the rest of the player game state.\n'
        '    _save_game_state_to_supabase(force=True)\n'
        '    return True, f"已領取 {_achievement_reward_text(item)}"\n'
    )
    s = s.replace(anchor, replacement, 1)

# 4) Load remote game state before any page renders.
if '# Load persistent player/slime state before rendering pages.' not in s:
    anchor = '\n\nrender_quick_scroll_nav()\n\npage = st.session_state.medslime_page\n'
    if anchor not in s:
        raise RuntimeError('page-dispatch start anchor not found')
    replacement = (
        '\n\n# Load persistent player/slime state before rendering pages.\n'
        '_load_game_state_from_supabase_once()\n'
        'render_quick_scroll_nav()\n\n'
        'page = st.session_state.medslime_page\n'
    )
    s = s.replace(anchor, replacement, 1)

# 5) Autosave any changed game state after a successful Streamlit rerun.
if '# Save any resource/slime changes made during this rerun.' not in s:
    anchor = '\nrender_quick_scroll_bottom()\n'
    if anchor not in s:
        raise RuntimeError('page-dispatch end anchor not found')
    replacement = (
        '\n# Save any resource/slime changes made during this rerun.\n'
        '_save_game_state_to_supabase_if_changed()\n'
        'render_quick_scroll_bottom()\n'
    )
    s = s.replace(anchor, replacement, 1)

p.write_text(s, encoding='utf-8')
