from pathlib import Path

p=Path('streamlit_app.py')
s=p.read_text(encoding='utf-8')

# 1) Make avatar rendering backward-compatible with the new 17-slime catalog.
s=s.replace('gradient = "linear-gradient(145deg,#66706b,#252d29)" if mystery else item["gradient"]', 'gradient = "linear-gradient(145deg,#66706b,#252d29)" if mystery else item.get("gradient", "linear-gradient(145deg,#9be7b5,#38c77a)")')

# 2) Give the new roster fallback gradients so home/focus/collection can all render before final art exists.
gradients={
'green':'linear-gradient(145deg,#a8efb6,#36c978)','blue':'linear-gradient(145deg,#b9defe,#579ce5)','yellow':'linear-gradient(145deg,#fff1a1,#e6ca45)','pink':'linear-gradient(145deg,#ffd0df,#ef8fb2)',
'latte':'linear-gradient(145deg,#ead6bb,#a87855)','burger':'linear-gradient(145deg,#ffd47d,#c87b3e)','sushi':'linear-gradient(145deg,#ffd4cf,#ee8d82)','boba':'linear-gradient(145deg,#d9b38c,#8a5c3b)','onigiri':'linear-gradient(145deg,#f7f7ef,#a7b5a7)','takoyaki':'linear-gradient(145deg,#eaa46f,#a95e38)',
'insomnia':'linear-gradient(145deg,#a8a8c7,#565b78)','melted':'linear-gradient(145deg,#b8d9cc,#6f9e8e)','outofbody':'linear-gradient(145deg,#d7ccf6,#8d75c9)','crying':'linear-gradient(145deg,#b9d8fa,#5f95d6)','error404':'linear-gradient(145deg,#92e4d2,#365e61)','deadinside':'linear-gradient(145deg,#bbb9b3,#696963)','chill':'linear-gradient(145deg,#bcd8c7,#46685d)'}
for theme, gradient in gradients.items():
    needle=f'"theme":"{theme}",'
    repl=f'"theme":"{theme}","gradient":"{gradient}",'
    s=s.replace(needle,repl,1)

# 3) Add dedicated collection styling so the page is not a pile of native controls.
css='''\n<style>\n.slime-v2-head{display:flex;justify-content:space-between;align-items:flex-end;gap:1rem;margin:.25rem 0 1rem}.slime-v2-title{font-size:2rem;font-weight:950;color:#17372a;letter-spacing:-.04em}.slime-v2-sub{color:#789083;font-size:.9rem;margin-top:.25rem}.slime-v2-res{white-space:nowrap;font-weight:850;color:#315b45}.slime-v2-card{border:1px solid #dbe9e1;background:rgba(255,255,255,.9);border-radius:20px;padding:.7rem;text-align:center;min-height:210px;box-shadow:0 8px 22px rgba(32,85,54,.05)}.slime-v2-card.locked{background:#f5f8f6}.slime-v2-card-name{font-weight:900;color:#1c4130;font-size:.88rem;min-height:2.3rem;margin-top:.25rem}.slime-v2-meta{font-size:.72rem;color:#789083;margin-top:.18rem}.slime-v2-detail{border:1px solid #dbe9e1;background:rgba(255,255,255,.94);border-radius:24px;padding:1.25rem;box-shadow:0 12px 28px rgba(32,85,54,.06);position:sticky;top:1rem}.slime-v2-detail-name{font-size:1.35rem;font-weight:950;color:#17372a;text-align:center;margin:.4rem 0}.slime-v2-rarity{text-align:center;color:#57a976;font-weight:900;font-size:.78rem}.slime-v2-summary{margin-top:1.5rem;border:1px solid #dbe9e1;background:rgba(255,255,255,.9);border-radius:22px;padding:1.15rem}@media(max-width:767px){.slime-v2-head{align-items:flex-start;flex-direction:column}.slime-v2-title{font-size:1.65rem}.slime-v2-detail{position:static}.slime-v2-card{min-height:180px;padding:.55rem}[data-testid="stHorizontalBlock"]:has([class*="st-key-slime_v2_"]) {gap:.55rem!important}}\n</style>\n'''
anchor='def slime_page():\n    topbar()'
if anchor in s and 'slime-v2-card{' not in s:
    s=s.replace(anchor,'def slime_page():\n    st.markdown('+repr(css)+', unsafe_allow_html=True)\n    topbar()',1)

# 4) Replace raw card/detail emoji rendering with existing slime avatar renderer.
s=s.replace('st.markdown(f"### {\'🔒\' if not owned else x[\'emoji\']}\\n**{title}** · {x[\'rarity\']}")\n                    st.caption("已擁有" if owned else "尚未取得")', 'avatar = slime_avatar_markup(x, size="card", locked=not owned, mystery=(x["rarity"]=="SSR" and not owned))\n                    st.markdown(f\'<div class="slime-v2-card{"" if owned else " locked"}">{avatar}<div class="slime-v2-card-name">{html.escape(title)}</div><div class="slime-v2-meta">{x["rarity"]} · {"已擁有" if owned else "尚未取得"}</div></div>\', unsafe_allow_html=True)')
s=s.replace('st.markdown(f"# {x[\'emoji\'] if owned else \'🔒\'}")\n        st.markdown(f"### {title}　`{x[\'rarity\']}`")', 'detail_avatar = slime_avatar_markup(x, size="home", locked=not owned, mystery=(x["rarity"]=="SSR" and not owned))\n        st.markdown(f\'<div class="slime-v2-detail">{detail_avatar}<div class="slime-v2-detail-name">{html.escape(title)}</div><div class="slime-v2-rarity">{x["rarity"]}</div></div>\', unsafe_allow_html=True)')

p.write_text(s,encoding='utf-8')
print('fixed slime page crash and styling')
