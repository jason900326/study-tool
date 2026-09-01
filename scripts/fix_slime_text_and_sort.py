from pathlib import Path

p = Path('streamlit_app.py')
s = p.read_text(encoding='utf-8')

old_css = '''.slime-v2-head{display:flex;justify-content:space-between;align-items:flex-end;gap:1rem;margin:.25rem 0 1rem}.slime-v2-title{font-size:2rem;font-weight:950;color:#17372a;letter-spacing:-.04em}.slime-v2-sub{color:#789083;font-size:.9rem;margin-top:.25rem}.slime-v2-res{white-space:nowrap;font-weight:850;color:#315b45}.slime-v2-card{border:1px solid #dbe9e1;background:rgba(255,255,255,.9);border-radius:20px;padding:.7rem;text-align:center;min-height:210px;box-shadow:0 8px 22px rgba(32,85,54,.05)}'''
new_css = '''.slime-v2-head{display:flex;justify-content:space-between;align-items:flex-end;gap:1rem;margin:.25rem 0 1rem}.slime-v2-title{font-size:2rem;font-weight:950;color:#17372a;letter-spacing:-.04em}.slime-v2-sub{color:#789083;font-size:.9rem;margin-top:.25rem}.slime-v2-res{white-space:nowrap;font-weight:850;color:#315b45}.slime-v2-page-marker{display:none}.slime-v2-card{border:1px solid #dbe9e1;background:rgba(255,255,255,.9);border-radius:20px;padding:.7rem;text-align:center;min-height:210px;box-shadow:0 8px 22px rgba(32,85,54,.05)}'''
if old_css not in s:
    raise RuntimeError('slime css anchor not found')
s = s.replace(old_css, new_css, 1)

old_tail = '''.slime-v2-summary{margin-top:1.5rem;border:1px solid #dbe9e1;background:rgba(255,255,255,.9);border-radius:22px;padding:1.15rem}@media(max-width:767px){'''
new_tail = '''.slime-v2-summary{margin-top:1.5rem;border:1px solid #dbe9e1;background:rgba(255,255,255,.9);border-radius:22px;padding:1.15rem}[data-testid="stMainBlockContainer"]:has(.slime-v2-page-marker) h1,[data-testid="stMainBlockContainer"]:has(.slime-v2-page-marker) h2,[data-testid="stMainBlockContainer"]:has(.slime-v2-page-marker) h3,[data-testid="stMainBlockContainer"]:has(.slime-v2-page-marker) h4,[data-testid="stMainBlockContainer"]:has(.slime-v2-page-marker) p,[data-testid="stMainBlockContainer"]:has(.slime-v2-page-marker) label,[data-testid="stMainBlockContainer"]:has(.slime-v2-page-marker) [data-testid="stCaptionContainer"]{color:#244c39!important}[data-testid="stMainBlockContainer"]:has(.slime-v2-page-marker) [data-testid="stCaptionContainer"] p{color:#789083!important}[data-testid="stMainBlockContainer"]:has(.slime-v2-page-marker) [data-testid="stMetricLabel"] p{color:#789083!important}[data-testid="stMainBlockContainer"]:has(.slime-v2-page-marker) [data-testid="stMetricValue"]{color:#17372a!important}@media(max-width:767px){'''
if old_tail not in s:
    raise RuntimeError('slime css tail anchor not found')
s = s.replace(old_tail, new_tail, 1)

old_top = '''    topbar()\n    render_back_button("返回首頁", "home", "back_slime")'''
new_top = '''    topbar()\n    st.markdown('<div class="slime-v2-page-marker"></div>', unsafe_allow_html=True)\n    render_back_button("返回首頁", "home", "back_slime")'''
if old_top not in s:
    raise RuntimeError('slime page top anchor not found')
s = s.replace(old_top, new_top, 1)

old_rank = '''    rank={"SSR":0,"SR":1,"R":2,"N":3}\n    if sort=="稀有度": visible.sort(key=lambda x:(rank[x["rarity"]],x["name"]))\n    elif sort=="是否擁有": visible.sort(key=lambda x:(x["name"] not in st.session_state.collection,rank[x["rarity"]]))\n    elif sort=="碎片數": visible.sort(key=lambda x:-st.session_state.slime_progress[x["name"]]["fragments"])\n    elif sort=="最近取得": visible.sort(key=lambda x:(x["name"] not in st.session_state.collection,-st.session_state.collection.index(x["name"]) if x["name"] in st.session_state.collection else 0))'''
new_rank = '''    rank={"N":0,"R":1,"SR":2,"SSR":3}\n    if sort=="稀有度": visible.sort(key=lambda x:(rank[x["rarity"]],x["name"]))\n    elif sort=="是否擁有": visible.sort(key=lambda x:(x["name"] not in st.session_state.collection,rank[x["rarity"]],x["name"]))\n    elif sort=="碎片數": visible.sort(key=lambda x:-st.session_state.slime_progress[x["name"]]["fragments"])\n    elif sort=="最近取得": visible.sort(key=lambda x:(x["name"] not in st.session_state.collection,-st.session_state.collection.index(x["name"]) if x["name"] in st.session_state.collection else 0))\n\n    # The active companion is always pinned first without changing the chosen sort order.\n    visible.sort(key=lambda x: x["name"] != st.session_state.selected_slime)'''
if old_rank not in s:
    raise RuntimeError('slime sort anchor not found')
s = s.replace(old_rank, new_rank, 1)

p.write_text(s, encoding='utf-8')
print('fixed slime text colors and sorting')
