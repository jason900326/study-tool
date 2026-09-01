from pathlib import Path

p = Path('streamlit_app.py')
s = p.read_text(encoding='utf-8')

old_css = '.slime-v2-card{border:1px solid #dbe9e1;background:rgba(255,255,255,.9);border-radius:20px;padding:.72rem;text-align:center;min-height:205px;box-shadow:0 8px 22px rgba(32,85,54,.05);overflow:hidden}.slime-v2-card.locked{background:#f5f8f6}'
new_css = '.slime-v2-card{border:1px solid #dbe9e1;background:rgba(255,255,255,.9);border-radius:20px;padding:.72rem;text-align:center;min-height:205px;box-shadow:0 8px 22px rgba(32,85,54,.05);overflow:hidden;transition:min-height .24s ease,padding .24s ease,box-shadow .24s ease,transform .24s ease}.slime-v2-card.expanded{min-height:390px;padding:1rem;box-shadow:0 16px 34px rgba(32,85,54,.12);transform:translateY(-2px);animation:slimeCardExpand .24s ease-out both}.slime-v2-card.locked{background:#f5f8f6}@keyframes slimeCardExpand{from{opacity:.94;transform:scale(.97)}to{opacity:1;transform:scale(1)}}'
assert old_css in s
s = s.replace(old_css, new_css, 1)

old_inline_css = '.slime-v2-card-frag{margin-top:.35rem;color:#557768;font-size:.7rem;font-weight:800;line-height:1.35}.slime-v2-inline-detail{margin:.55rem 0 .2rem;border:1px solid #d8e9df;background:rgba(255,255,255,.98);border-radius:16px;padding:.8rem .75rem;text-align:left;box-shadow:0 10px 24px rgba(32,85,54,.09);animation:slimeDetailPop .22s ease-out both;transform-origin:top center;overflow:hidden}.slime-v2-inline-title{font-size:.88rem;font-weight:950;color:#17372a;margin-bottom:.2rem}.slime-v2-inline-copy{font-size:.72rem;line-height:1.45;color:#6f887b;margin-bottom:.55rem}.slime-v2-inline-row{display:flex;justify-content:space-between;gap:.5rem;align-items:center;font-size:.72rem;color:#557768;margin:.28rem 0}.slime-v2-inline-row strong{color:#244c39}.slime-v2-inline-track{height:6px;border-radius:999px;background:#e6eee9;overflow:hidden;margin:.4rem 0 .5rem}.slime-v2-inline-fill{height:100%;border-radius:999px;background:#55b97b}.slime-v2-inline-accessory{font-size:.72rem;color:#315b45;font-weight:850;margin-top:.45rem}@keyframes slimeDetailPop{from{opacity:0;transform:translateY(-8px) scale(.97)}to{opacity:1;transform:translateY(0) scale(1)}}'
new_inline_css = '.slime-v2-card-frag{margin-top:.35rem;color:#557768;font-size:.7rem;font-weight:800;line-height:1.35}.slime-v2-expanded-body{margin-top:.75rem;padding-top:.7rem;border-top:1px solid #e1ece6;text-align:left}.slime-v2-expanded-copy{font-size:.74rem;line-height:1.55;color:#6f887b;margin-bottom:.65rem}.slime-v2-expanded-label{display:flex;align-items:center;justify-content:space-between;gap:.5rem;font-size:.72rem;color:#557768;margin:.35rem 0}.slime-v2-expanded-label strong{color:#244c39}.slime-v2-expanded-track{height:7px;border-radius:999px;background:#e6eee9;overflow:hidden;margin:.35rem 0 .55rem}.slime-v2-expanded-fill{height:100%;background:#55b97b;border-radius:999px}.slime-v2-expanded-accessory{margin-top:.6rem;padding:.55rem .6rem;border-radius:12px;background:#f3f8f5;color:#315b45;font-size:.74rem;font-weight:850}.slime-v2-expanded-status{margin-top:.35rem;font-size:.68rem;color:#789083;line-height:1.4}'
assert old_inline_css in s
s = s.replace(old_inline_css, new_inline_css, 1)

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

                card_class = f'slime-v2-card{"" if owned else " locked"}{" expanded" if detail_open else ""}'
                st.markdown(
                    f'<div class="{card_class}">{avatar}<div class="slime-v2-card-name">{html.escape(title)}</div>'
                    f'<div class="slime-v2-meta">{x["rarity"]} · {"已擁有" if owned else "尚未取得"}</div>{companion_line}{expanded_body}</div>',
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
