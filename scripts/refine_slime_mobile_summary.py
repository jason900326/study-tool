from pathlib import Path

p = Path('streamlit_app.py')
s = p.read_text(encoding='utf-8')

old_css = '.slime-v2-rarity{text-align:center;color:#57a976;font-weight:900;font-size:.78rem}.slime-v2-summary{margin-top:1.5rem;border:1px solid #dbe9e1;background:rgba(255,255,255,.9);border-radius:22px;padding:1.15rem}'
new_css = '.slime-v2-rarity{text-align:center;color:#57a976;font-weight:900;font-size:.78rem}.slime-v2-companion-badge{display:inline-flex;align-items:center;gap:.3rem;margin:.45rem auto 0;padding:.34rem .72rem;border-radius:999px;background:#e9f8ef;border:1px solid #cfe9da;color:#28754b;font-size:.78rem;font-weight:900}.slime-v2-summary{margin-top:1.5rem;border:1px solid #dbe9e1;background:rgba(255,255,255,.94);border-radius:24px;padding:1.2rem 1.25rem;box-shadow:0 10px 28px rgba(32,85,54,.06)}.slime-v2-summary-title{font-size:1.25rem;font-weight:950;color:#17372a;margin-bottom:.2rem}.slime-v2-summary-main{font-size:1rem;font-weight:850;color:#315b45;margin-bottom:.55rem}.slime-v2-summary-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.65rem;margin-top:1rem}.slime-v2-summary-item{border:1px solid #e0ece5;background:#f8fbf9;border-radius:16px;padding:.8rem .7rem}.slime-v2-summary-label{font-size:.72rem;color:#789083;font-weight:850}.slime-v2-summary-value{font-size:1.1rem;color:#17372a;font-weight:950;margin-top:.16rem}.slime-v2-summary-foot{margin-top:.85rem;color:#789083;font-size:.82rem;font-weight:800}'
assert old_css in s
s = s.replace(old_css, new_css, 1)

old_mobile = '@media(max-width:767px){.slime-v2-head{align-items:flex-start;flex-direction:column}.slime-v2-title{font-size:1.65rem}.slime-v2-detail{position:static}.slime-v2-card{min-height:180px;padding:.55rem}[data-testid="stHorizontalBlock"]:has([class*="st-key-slime_v2_"]) {gap:.55rem!important}}'
new_mobile = '@media(max-width:767px){.slime-v2-head{align-items:flex-start;flex-direction:column}.slime-v2-title{font-size:1.65rem}.slime-v2-detail{position:static}.slime-v2-card{min-height:180px;padding:.55rem}.slime-v2-summary{padding:1rem}.slime-v2-summary-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:.55rem}.slime-v2-summary-item{padding:.72rem .68rem}[data-testid="stHorizontalBlock"]:has([class*="st-key-slime_v2_"]) {gap:.55rem!important}}'
assert old_mobile in s
s = s.replace(old_mobile, new_mobile, 1)

old_detail = '''        detail_avatar = slime_avatar_markup(x, size="home", locked=not owned, mystery=(x["rarity"]=="SSR" and not owned))
        st.markdown(f'<div class="slime-v2-detail">{detail_avatar}<div class="slime-v2-detail-name">{html.escape(title)}</div><div class="slime-v2-rarity">{x["rarity"]}</div></div>', unsafe_allow_html=True)
        st.write(x["tagline"] if owned or x["rarity"]!="SSR" else "取得後才會揭曉真正身分。")
        if owned:
            if x["name"]==st.session_state.selected_slime: st.button("✓ 目前陪伴中",disabled=True,use_container_width=True)
            elif st.button("設為陪伴史萊姆",type="primary",use_container_width=True): st.session_state.selected_slime=x["name"]; st.rerun()
'''
new_detail = '''        detail_avatar = slime_avatar_markup(x, size="home", locked=not owned, mystery=(x["rarity"]=="SSR" and not owned))
        companion_badge = '<div style="text-align:center"><span class="slime-v2-companion-badge">✓ 陪伴中</span></div>' if owned and x["name"]==st.session_state.selected_slime else ''
        st.markdown(f'<div class="slime-v2-detail">{detail_avatar}<div class="slime-v2-detail-name">{html.escape(title)}</div><div class="slime-v2-rarity">{x["rarity"]}</div>{companion_badge}</div>', unsafe_allow_html=True)
        st.write(x["tagline"] if owned or x["rarity"]!="SSR" else "取得後才會揭曉真正身分。")
        if owned:
            if x["name"]!=st.session_state.selected_slime and st.button("設為陪伴史萊姆",type="primary",use_container_width=True): st.session_state.selected_slime=x["name"]; st.rerun()
'''
assert old_detail in s
s = s.replace(old_detail, new_detail, 1)

old_summary = '''    owned=len([x for x in SLIME_CATALOG if x["name"] in st.session_state.collection])
    st.divider(); st.markdown("### 收藏進度"); st.progress(owned/17,text=f"{owned} / 17")
    cols=st.columns(4)
    for c,r in zip(cols,["N","R","SR","SSR"]):
        got=sum(1 for x in SLIME_CATALOG if x["rarity"]==r and x["name"] in st.session_state.collection); total=sum(1 for x in SLIME_CATALOG if x["rarity"]==r)
        c.metric(r,f"{got} / {total}")
    st.caption(f"專屬飾品：{sum(1 for v in st.session_state.slime_accessories.values() if v)} / 17")
'''
new_summary = '''    owned=len([x for x in SLIME_CATALOG if x["name"] in st.session_state.collection])
    accessory_owned=sum(1 for v in st.session_state.slime_accessories.values() if v)
    rarity_parts=[]
    for r in ["N","R","SR","SSR"]:
        got=sum(1 for x in SLIME_CATALOG if x["rarity"]==r and x["name"] in st.session_state.collection)
        total=sum(1 for x in SLIME_CATALOG if x["rarity"]==r)
        rarity_parts.append(f'<div class="slime-v2-summary-item"><div class="slime-v2-summary-label">{r}</div><div class="slime-v2-summary-value">{got} / {total}</div></div>')
    st.markdown(
        f'<div class="slime-v2-summary"><div class="slime-v2-summary-title">收藏進度</div><div class="slime-v2-summary-main">{owned} / 17 · {round(owned/17*100)}%</div>'
        f'<div class="slime-v2-summary-grid">{"".join(rarity_parts)}</div><div class="slime-v2-summary-foot">✨ 專屬飾品 {accessory_owned} / 17</div></div>',
        unsafe_allow_html=True,
    )
    st.progress(owned/17)
'''
assert old_summary in s
s = s.replace(old_summary, new_summary, 1)

p.write_text(s, encoding='utf-8')
