from pathlib import Path

app = Path('streamlit_app.py')
s = app.read_text(encoding='utf-8')

# Session state for per-slime equipped accessory status.
anchor = '    "slime_accessories": {},\n'
if '"slime_accessory_equipped": {}' not in s:
    if anchor not in s:
        raise RuntimeError('slime_accessories default anchor missing')
    s = s.replace(anchor, anchor + '    "slime_accessory_equipped": {},\n', 1)

# Ensure mapping exists on slime page.
anchor = '    st.session_state.setdefault("slime_accessories",{})\n'
if 'st.session_state.setdefault("slime_accessory_equipped",{})' not in s:
    if anchor not in s:
        raise RuntimeError('slime page accessory anchor missing')
    s = s.replace(anchor, anchor + '    st.session_state.setdefault("slime_accessory_equipped",{})\n', 1)

# Expanded card status includes equipped state.
old = '''                        acc=st.session_state.slime_accessories.setdefault(x["name"],False)\n                        remain=max(0,30-frag)\n                        pct=max(0,min(100,round(frag/30*100)))\n                        if acc:\n                            status='專屬飾品已解鎖'\n                        elif frag>=30:\n'''
new = '''                        acc=st.session_state.slime_accessories.setdefault(x["name"],False)\n                        equipped=bool(st.session_state.slime_accessory_equipped.setdefault(x["name"],False) and acc)\n                        remain=max(0,30-frag)\n                        pct=max(0,min(100,round(frag/30*100)))\n                        if equipped:\n                            status='專屬飾品已裝備'\n                        elif acc:\n                            status='專屬飾品已解鎖'\n                        elif frag>=30:\n'''
if old not in s:
    raise RuntimeError('expanded accessory status block missing')
s = s.replace(old, new, 1)

# Add equip / unequip button and keep unlock logic.
old = '''                        if not acc and st.button("解鎖專屬飾品",disabled=frag<30,use_container_width=True,key=f"unlock_accessory_{x['theme']}"):\n                            st.session_state.slime_progress[x["name"]]["fragments"]-=30\n                            st.session_state.slime_accessories[x["name"]]=True\n                            st.rerun()\n'''
new = '''                        if acc:\n                            equipped = bool(st.session_state.slime_accessory_equipped.get(x["name"], False))\n                            if st.button(\n                                "卸下專屬飾品" if equipped else "裝備專屬飾品",\n                                use_container_width=True,\n                                key=f"toggle_accessory_{x['theme']}",\n                            ):\n                                st.session_state.slime_accessory_equipped[x["name"]] = not equipped\n                                st.rerun()\n                        elif st.button("解鎖專屬飾品",disabled=frag<30,use_container_width=True,key=f"unlock_accessory_{x['theme']}"):\n                            st.session_state.slime_progress[x["name"]]["fragments"]-=30\n                            st.session_state.slime_accessories[x["name"]]=True\n                            st.session_state.slime_accessory_equipped[x["name"]]=False\n                            st.rerun()\n'''
if old not in s:
    raise RuntimeError('unlock accessory block missing')
s = s.replace(old, new, 1)

# Add equipped state to persistent snapshot.
old = '''    accessories = st.session_state.setdefault("slime_accessories", {})\n    nicknames = st.session_state.setdefault("slime_nicknames", {})\n    slimes = []\n'''
new = '''    accessories = st.session_state.setdefault("slime_accessories", {})\n    equipped_accessories = st.session_state.setdefault("slime_accessory_equipped", {})\n    nicknames = st.session_state.setdefault("slime_nicknames", {})\n    slimes = []\n'''
if old not in s:
    raise RuntimeError('snapshot accessory maps anchor missing')
s = s.replace(old, new, 1)

old = '''                "accessory_unlocked": bool(accessories.get(name, False)),\n                "nickname": nickname,\n'''
new = '''                "accessory_unlocked": bool(accessories.get(name, False)),\n                "accessory_equipped": bool(accessories.get(name, False) and equipped_accessories.get(name, False)),\n                "nickname": nickname,\n'''
if old not in s:
    raise RuntimeError('snapshot slime accessory field anchor missing')
s = s.replace(old, new, 1)

# Load equipped field from Supabase.
old = '.select("slime_name,owned,fragments,accessory_unlocked,nickname,acquired_order")'
new = '.select("slime_name,owned,fragments,accessory_unlocked,accessory_equipped,nickname,acquired_order")'
if old not in s:
    raise RuntimeError('player_slimes select anchor missing')
s = s.replace(old, new, 1)

old = '''            accessories = st.session_state.setdefault("slime_accessories", {})\n            nicknames = st.session_state.setdefault("slime_nicknames", {})\n            for slime_row in valid_rows:\n'''
new = '''            accessories = st.session_state.setdefault("slime_accessories", {})\n            equipped_accessories = st.session_state.setdefault("slime_accessory_equipped", {})\n            nicknames = st.session_state.setdefault("slime_nicknames", {})\n            for slime_row in valid_rows:\n'''
if old not in s:
    raise RuntimeError('load accessory maps anchor missing')
s = s.replace(old, new, 1)

old = '''                accessories[name] = bool(slime_row.get("accessory_unlocked", False))\n                nickname = str(slime_row.get("nickname") or "").strip()\n'''
new = '''                accessories[name] = bool(slime_row.get("accessory_unlocked", False))\n                equipped_accessories[name] = bool(accessories[name] and slime_row.get("accessory_equipped", False))\n                nickname = str(slime_row.get("nickname") or "").strip()\n'''
if old not in s:
    raise RuntimeError('load equipped state anchor missing')
s = s.replace(old, new, 1)

app.write_text(s, encoding='utf-8')

# Keep the original game-state setup safe to re-run for new deployments.
sql = Path('supabase/game_state_mvp.sql')
q = sql.read_text(encoding='utf-8')
if 'accessory_equipped boolean' not in q:
    q = q.replace('    accessory_unlocked boolean not null default false,\n', '    accessory_unlocked boolean not null default false,\n    accessory_equipped boolean not null default false,\n', 1)
    marker = 'create index if not exists player_slimes_user_key_idx\n'
    migration = 'alter table public.player_slimes\n    add column if not exists accessory_equipped boolean not null default false;\n\n'
    if marker not in q:
        raise RuntimeError('game_state SQL migration anchor missing')
    q = q.replace(marker, migration + marker, 1)
sql.write_text(q, encoding='utf-8')
