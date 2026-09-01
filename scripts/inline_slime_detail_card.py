from pathlib import Path

p = Path('streamlit_app.py')
s = p.read_text(encoding='utf-8')

# Add a compact animated inline detail card that expands directly under the clicked button.
old_css = '.slime-v2-card-frag{margin-top:.35rem;color:#557768;font-size:.7rem;font-weight:800;line-height:1.35}.slime-v2-detail{border:1px solid #dbe9e1;background:rgba(255,255,255,.94);border-radius:24px;padding:1.25rem;box-shadow:0 12px 28px rgba(32,85,54,.06);position:sticky;top:1rem}'
new_css = '.slime-v2-card-frag{margin-top:.35rem;color:#557768;font-size:.7rem;font-weight:800;line-height:1.35}.slime-v2-inline-detail{margin:.55rem 0 .2rem;border:1px solid #d8e9df;background:rgba(255,255,255,.98);border-radius:16px;padding:.8rem .75rem;text-align:left;box-shadow:0 10px 24px rgba(32,85,54,.09);animation:slimeDetailPop .22s ease-out both;transform-origin:top center;overflow:hidden}.slime-v2-inline-title{font-size:.88rem;font-weight:950;color:#17372a;margin-bottom:.2rem}.slime-v2-inline-copy{font-size:.72rem;line-height:1.45;color:#6f887b;margin-bottom:.55rem}.slime-v2-inline-row{display:flex;justify-content:space-between;gap:.5rem;align-items:center;font-size:.72rem;color:#557768;margin:.28rem 0}.slime-v2-inline-row strong{color:#244c39}.slime-v2-inline-track{height:6px;border-radius:999px;background:#e6eee9;overflow:hidden;margin:.4rem 0 .5rem}.slime-v2-inline-fill{height:100%;border-radius:999px;background:#55b97b}.slime-v2-inline-accessory{font-size:.72rem;color:#315b45;font-weight:850;margin-top:.45rem}@keyframes slimeDetailPop{from{opacity:0;transform:translateY(-8px) scale(.97)}to{opacity:1;transform:translateY(0) scale(1)}}.slime-v2-detail{border:1px solid #dbe9e1;background:rgba(255,255,255,.94);border-radius:24px;padding:1.25rem;box-shadow:0 12px 28px rgba(32,85,54,.06);position:sticky;top:1rem}'
assert old_css in s
s = s.replace(old_css, new_css, 1)

old_grid = '''                if st.button("查看詳情",key=f"slime_v2_{x['theme']}",use_container_width=True):
                    st.session_state.slime_detail_name=x["name"]
                    st.rerun()

    detail_name = st.session_state.get("slime_detail_name")
    if detail_name in SLIME_BY_NAME:
        x=SLIME_BY_NAME[detail_name]
        owned=x["name"] in st.session_state.collection
        title="???" if x["rarity"]=="SSR" and not owned else x["name"]
        detail_avatar=slime_avatar_markup(x,size="home",locked=not owned,mystery=(x["rarity"]=="SSR" and not owned))
        companion_badge='<div style="text-align:center"><span class="slime-v2-companion-badge">✓ 陪伴中</span></div>' if owned and x["name"]==st.session_state.selected_slime else ''
        st.markdown(f'<div class="slime-v2-detail" style="position:static;margin-top:1rem">{detail_avatar}<div class="slime-v2-detail-name">{html.escape(title)}</div><div class="slime-v2-rarity">{x["rarity"]}</div>{companion_badge}</div>',unsafe_allow_html=True)
        st.write(x["tagline"] if owned or x["rarity"]!="SSR" else "取得後才會揭曉真正身分。")
        if owned:
            if x["name"]!=st.session_state.selected_slime and st.button("設為陪伴史萊姆",type="primary",use_container_width=True,key=f"set_companion_{x['theme']}"):
                st.session_state.selected_slime=x["name"]
                st.rerun()
            frag=st.session_state.slime_progress[x["name"]]["fragments"]
            st.markdown("#### 專屬碎片")
            st.progress(min(1.0,frag/30),text=f"{frag} / 30")
            remain=max(0,30-frag)
            acc=st.session_state.slime_accessories.setdefault(x["name"],False)
            if acc:
                st.caption("專屬飾品已解鎖")
            elif frag>=30:
                st.caption("已可解鎖專屬飾品")
            else:
                st.caption(f"專屬飾品還差 {remain} 碎片")
            st.markdown(f"#### 專屬飾品\\n✨ **{x['accessory']}**")
            if not acc:
                if st.button("解鎖專屬飾品",disabled=frag<30,use_container_width=True,key=f"unlock_accessory_{x['theme']}"):
                    st.session_state.slime_progress[x["name"]]["fragments"]-=30
                    st.session_state.slime_accessories[x["name"]]=True
                    st.rerun()
            else:
                st.success("已解鎖")
        else:
            st.info("取得這隻史萊姆後，即可累積專屬碎片、設為陪伴並解鎖專屬飾品。")
'''

new_grid = '''                detail_open = st.session_state.get("slime_detail_name") == x["name"]
                if st.button("收起詳情" if detail_open else "查看詳情",key=f"slime_v2_{x['theme']}",use_container_width=True):
                    st.session_state.slime_detail_name = None if detail_open else x["name"]
                    st.rerun()
                if st.session_state.get("slime_detail_name") == x["name"]:
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
                        st.markdown(
                            f'<div class="slime-v2-inline-detail"><div class="slime-v2-inline-title">目前狀態</div>'
                            f'<div class="slime-v2-inline-copy">{html.escape(x["tagline"])}</div>'
                            f'<div class="slime-v2-inline-row"><span>專屬碎片</span><strong>{frag} / 30</strong></div>'
                            f'<div class="slime-v2-inline-track"><div class="slime-v2-inline-fill" style="width:{pct}%"></div></div>'
                            f'<div class="slime-v2-inline-row"><span>解鎖進度</span><strong>{html.escape(status)}</strong></div>'
                            f'<div class="slime-v2-inline-accessory">✨ {html.escape(x["accessory"])}</div></div>',
                            unsafe_allow_html=True,
                        )
                        if x["name"]!=st.session_state.selected_slime:
                            if st.button("設為陪伴",type="primary",use_container_width=True,key=f"set_companion_{x['theme']}"):
                                st.session_state.selected_slime=x["name"]
                                st.rerun()
                        if not acc and st.button("解鎖專屬飾品",disabled=frag<30,use_container_width=True,key=f"unlock_accessory_{x['theme']}"):
                            st.session_state.slime_progress[x["name"]]["fragments"]-=30
                            st.session_state.slime_accessories[x["name"]]=True
                            st.rerun()
                    else:
                        locked_copy = "取得後才會揭曉真正身分。" if x["rarity"]=="SSR" else "取得這隻史萊姆後，即可累積專屬碎片、設為陪伴並解鎖專屬飾品。"
                        st.markdown(
                            f'<div class="slime-v2-inline-detail"><div class="slime-v2-inline-title">尚未取得</div><div class="slime-v2-inline-copy">{html.escape(locked_copy)}</div></div>',
                            unsafe_allow_html=True,
                        )
'''
assert old_grid in s
s = s.replace(old_grid, new_grid, 1)

p.write_text(s, encoding='utf-8')
