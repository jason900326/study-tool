from pathlib import Path

p = Path('streamlit_app.py')
s = p.read_text(encoding='utf-8')

# Keep slime artwork proportional at all widths.
s = s.replace(
    '.slime-v2-card .official-slime-art-card{width:100%;max-width:128px;height:104px;margin:0 auto}.slime-v2-card .catalog-slime-card{width:100%;max-width:128px;height:104px;margin:0 auto}',
    '.slime-v2-card .official-slime-art-card{width:min(100%,128px);max-width:128px;aspect-ratio:1.23/1;height:auto;margin:0 auto}.slime-v2-card .catalog-slime-card{width:min(100%,128px);max-width:128px;aspect-ratio:1.23/1;height:auto;margin:0 auto}',
    1,
)

# Do not preload a detail view; details appear only after pressing 查看詳情.
s = s.replace(
    '    st.session_state.setdefault("slime_detail_name",st.session_state.selected_slime)\n',
    '    st.session_state.setdefault("slime_detail_name",None)\n',
    1,
)

# Remove duplicate resource line below rarity controls.
s = s.replace('    st.caption(f"🪙 {st.session_state.coins:,}　🎟️ {st.session_state.tickets:,}")\n\n', '\n', 1)

start = s.index('    left,right=st.columns([2.1,1],gap="large")\n', s.index('def slime_page():'))
end = s.index('\n\n\ndef achievements_page():', start)

new_block = '''    # Full-width collection grid. Detail content opens below only after the user asks for it.
    for start in range(0,len(visible),4):
        cols=st.columns(4)
        for i,col in enumerate(cols):
            if start+i>=len(visible): continue
            x=visible[start+i]; owned=x["name"] in st.session_state.collection
            title="???" if x["rarity"]=="SSR" and not owned else x["name"]
            frag=st.session_state.slime_progress[x["name"]]["fragments"]
            with col:
                avatar = slime_avatar_markup(x, size="card", locked=not owned, mystery=(x["rarity"]=="SSR" and not owned))
                is_companion = owned and x["name"] == st.session_state.selected_slime
                companion_line = '<div class="slime-v2-card-companion">✓ 陪伴中</div>' if is_companion else ''
                st.markdown(f'<div class="slime-v2-card{"" if owned else " locked"}">{avatar}<div class="slime-v2-card-name">{html.escape(title)}</div><div class="slime-v2-meta">{x["rarity"]} · {"已擁有" if owned else "尚未取得"}</div>{companion_line}</div>', unsafe_allow_html=True)
                if owned and not is_companion:
                    st.progress(min(1.0,frag/30),text=f"碎片 {frag} / 30")
                if st.button("查看詳情",key=f"slime_v2_{x['theme']}",use_container_width=True):
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

s = s[:start] + new_block + s[end:]
p.write_text(s, encoding='utf-8')
