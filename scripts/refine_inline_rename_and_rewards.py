from pathlib import Path

p = Path('streamlit_app.py')
s = p.read_text(encoding='utf-8')

# 1) Home: show only the user's nickname for the companion, not the canonical species name.
old = '''        st.markdown('<div class="home-slime-card">' + slime_avatar_markup(companion_item, size="home") + f'<div class="home-slime-label">{html.escape(companion_nickname)}</div><div class="muted">{html.escape(st.session_state.selected_slime)} · 陪伴中</div></div>', unsafe_allow_html=True)'''
new = '''        st.markdown('<div class="home-slime-card">' + slime_avatar_markup(companion_item, size="home") + f'<div class="home-slime-label">{html.escape(companion_nickname)}</div></div>', unsafe_allow_html=True)'''
if old not in s:
    raise RuntimeError('home companion anchor not found')
s = s.replace(old, new, 1)

# 2) Hide pull-rate text from the gacha page. Logic remains unchanged.
old = '''    st.caption("機率：N 32% · R 38% · SR 27% · SSR 3%")\n'''
if old not in s:
    raise RuntimeError('gacha rate caption anchor not found')
s = s.replace(old, '', 1)

# 3) Correct the post-30-fragment refund table.
old = '''                refund = {"N": 10, "R": 20, "SR": 40, "SSR": 80}[result["rarity"]]'''
new = '''                refund = {"N": 5, "R": 10, "SR": 20, "SSR": 50}[result["rarity"]]'''
if old not in s:
    raise RuntimeError('refund map anchor not found')
s = s.replace(old, new, 1)

# 4) Add CSS for real inline nickname editing in the card title position.
css_anchor = '''.slime-v2-card-frag{margin-top:.35rem;color:#557768;font-size:.7rem;font-weight:800;line-height:1.35}.slime-v2-expanded-body'''
css_replacement = '''.slime-v2-card-frag{margin-top:.35rem;color:#557768;font-size:.7rem;font-weight:800;line-height:1.35}[class*="st-key-slime_card_shell_"]{border:1px solid #dbe9e1;background:rgba(255,255,255,.9);border-radius:20px;padding:.72rem;text-align:center;min-height:205px;box-shadow:0 8px 22px rgba(32,85,54,.05);overflow:hidden;transition:min-height .24s ease,padding .24s ease,box-shadow .24s ease,transform .24s ease}[class*="st-key-slime_card_shell_"]:has([class*="st-key-inline_name_"]){min-height:390px;padding:1rem;box-shadow:0 16px 34px rgba(32,85,54,.12);transform:translateY(-2px);animation:slimeCardExpand .24s ease-out both}[class*="st-key-slime_card_shell_"] .official-slime-art-card,[class*="st-key-slime_card_shell_"] .catalog-slime-card{margin:0 auto}[class*="st-key-inline_name_"]{position:relative;margin:.15rem auto .05rem!important;max-width:100%}[class*="st-key-inline_name_"] input{background:transparent!important;border:0!important;box-shadow:none!important;text-align:center!important;font-weight:900!important;color:#1c4130!important;font-size:.9rem!important;padding:.15rem 1.7rem .15rem .35rem!important;min-height:2rem!important}[class*="st-key-inline_name_"] input:focus{background:#f5faf7!important;box-shadow:0 0 0 1px #cfe7d8!important;border-radius:9px!important}[class*="st-key-inline_name_"]::after{content:"✏️";position:absolute;right:.45rem;top:50%;transform:translateY(-50%);font-size:.78rem;pointer-events:none}.slime-v2-expanded-body'''
if css_anchor not in s:
    raise RuntimeError('slime inline css anchor not found')
s = s.replace(css_anchor, css_replacement, 1)

# 5) Replace the card rendering block so editing happens exactly where the name is shown.
start = s.index('            with col:\n                avatar = slime_avatar_markup', s.index('def slime_page():'))
end = s.index('\n\n\ndef achievements_page():', start)
new_block = '''            with col:
                avatar = slime_avatar_markup(x, size="card", locked=not owned, mystery=(x["rarity"]=="SSR" and not owned))
                is_companion = owned and x["name"] == st.session_state.selected_slime
                companion_line = '<div class="slime-v2-card-companion">✓ 陪伴中</div>' if is_companion else ''
                detail_open = st.session_state.get("slime_detail_name") == x["name"]

                expanded_body = ''
                if detail_open:
                    if owned:
                        acc=st.session_state.slime_accessories.setdefault(x["name"],False)
                        remain=max(0,30-frag)
                        pct=max(0,min(100,round(frag/30*100)))
                        if acc:
                            status='專屬飾品已解鎖'
                        elif frag>=30:
                            status='已可解鎖專屬飾品'
                        else:
                            status=f'專屬飾品還差 {remain} 碎片'
                        expanded_body = (
                            f'<div class="slime-v2-expanded-body">'
                            f'<div class="slime-v2-expanded-copy">{html.escape(x["tagline"])}</div>'
                            f'<div class="slime-v2-expanded-label"><span>專屬碎片</span><strong>{frag} / 30</strong></div>'
                            f'<div class="slime-v2-expanded-track"><div class="slime-v2-expanded-fill" style="width:{pct}%"></div></div>'
                            f'<div class="slime-v2-expanded-status">{html.escape(status)}</div>'
                            f'<div class="slime-v2-expanded-accessory">✨ 專屬飾品：{html.escape(x["accessory"])}</div>'
                            f'</div>'
                        )
                    else:
                        locked_copy = "取得後才會揭曉真正身分。" if x["rarity"]=="SSR" else "取得這隻史萊姆後，即可累積專屬碎片、設為陪伴並解鎖專屬飾品。"
                        expanded_body = f'<div class="slime-v2-expanded-body"><div class="slime-v2-expanded-copy">{html.escape(locked_copy)}</div></div>'

                def _save_inline_name(canonical_name, widget_key):
                    cleaned = str(st.session_state.get(widget_key, "") or "").strip()
                    if cleaned:
                        st.session_state.slime_nicknames[canonical_name] = cleaned
                    else:
                        st.session_state[widget_key] = get_slime_nickname(canonical_name)

                with st.container(key=f"slime_card_shell_{x['theme']}"):
                    st.markdown(avatar, unsafe_allow_html=True)
                    if detail_open and owned:
                        inline_key = f"inline_name_{x['theme']}"
                        current_nickname = get_slime_nickname(x["name"])
                        if inline_key not in st.session_state:
                            st.session_state[inline_key] = current_nickname
                        st.text_input(
                            "史萊姆名稱",
                            key=inline_key,
                            max_chars=20,
                            label_visibility="collapsed",
                            on_change=_save_inline_name,
                            args=(x["name"], inline_key),
                        )
                    else:
                        display_title = get_slime_nickname(x["name"]) if owned else title
                        st.markdown(f'<div class="slime-v2-card-name">{html.escape(display_title)}</div>', unsafe_allow_html=True)

                    st.markdown(
                        f'<div class="slime-v2-meta">{x["rarity"]} · {"已擁有" if owned else "尚未取得"}</div>{companion_line}{expanded_body}',
                        unsafe_allow_html=True,
                    )

                    if st.button("收起詳情" if detail_open else "查看詳情",key=f"slime_v2_{x['theme']}",use_container_width=True):
                        st.session_state.slime_detail_name = None if detail_open else x["name"]
                        st.rerun()

                    if detail_open and owned:
                        acc=st.session_state.slime_accessories.setdefault(x["name"],False)
                        if x["name"]!=st.session_state.selected_slime:
                            if st.button("設為陪伴",type="primary",use_container_width=True,key=f"set_companion_{x['theme']}"):
                                st.session_state.selected_slime=x["name"]
                                st.rerun()
                        if not acc and st.button("解鎖專屬飾品",disabled=frag<30,use_container_width=True,key=f"unlock_accessory_{x['theme']}"):
                            st.session_state.slime_progress[x["name"]]["fragments"]-=30
                            st.session_state.slime_accessories[x["name"]]=True
                            st.rerun()
'''
s = s[:start] + new_block + s[end:]

p.write_text(s, encoding='utf-8')
print('inline rename, home nickname, hidden rates, corrected refunds')
