from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

old_css = '''    .choice-card { background:rgba(255,255,255,.96); border:1px solid #dceae2; border-radius:25px; padding:1.45rem 1.5rem; min-height:156px; box-shadow:0 12px 28px rgba(30,78,50,.055); }\n    .choice-icon-shell { width:50px; height:50px; border-radius:15px; display:flex; align-items:center; justify-content:center; background:linear-gradient(145deg,#e8f9ee,#f1fbf5); border:1px solid #d7eadf; margin-bottom:.9rem; }\n'''
new_css = '''    .choice-card { background:rgba(255,255,255,.96); border:1px solid #dceae2; border-radius:25px; padding:1.45rem 1.5rem; height:196px; box-sizing:border-box; box-shadow:0 12px 28px rgba(30,78,50,.055); display:flex; flex-direction:column; }\n    .choice-icon-shell { width:50px; height:50px; min-height:50px; border-radius:15px; display:flex; align-items:center; justify-content:center; background:linear-gradient(145deg,#e8f9ee,#f1fbf5); border:1px solid #d7eadf; margin-bottom:.9rem; }\n'''
if old_css not in text:
    raise RuntimeError('choice-card css anchor not found')
text = text.replace(old_css, new_css, 1)

old_copy = '''    .choice-copy { color:#70877a; line-height:1.55; margin-top:.42rem; }\n    .study-header { margin:.35rem 0 1.2rem; }\n'''
new_copy = '''    .choice-copy { color:#70877a; line-height:1.55; margin-top:.42rem; }\n    [class*="st-key-study_choice_"] { margin-bottom:1.55rem; }\n    [class*="st-key-study_choice_"] > div { height:100%; }\n    [class*="st-key-study_choice_"] [data-testid="stButton"] { margin-top:.55rem; }\n    .study-page-transition-anchor { height:0; overflow:hidden; }\n    .block-container:has(.study-page-transition-anchor) { animation:studyPageIn .22s ease-out both; }\n    .block-container:has(.study-page-transition-anchor) [class*="st-key-study_choice_"] { animation:none !important; }\n    .block-container:has(.study-page-transition-anchor):has([class*="st-key-go_"] button:active) { opacity:.72; transform:translateY(2px); transition:opacity .10s ease,transform .10s ease; }\n    .study-header { margin:.35rem 0 1.2rem; }\n'''
if old_copy not in text:
    raise RuntimeError('choice-copy css anchor not found')
text = text.replace(old_copy, new_copy, 1)

old_anim = '''    .home-copy-card,.home-slime-card,.home-task,.choice-card,.study-header,.intro-panel { animation:pageIn .20s ease-out both; }\n    @keyframes drawerIn { from { transform:translateX(-18px); opacity:0; } to { transform:translateX(0); opacity:1; } }\n    @keyframes pageIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }\n'''
new_anim = '''    .home-copy-card,.home-slime-card,.home-task,.intro-panel { animation:pageIn .20s ease-out both; }\n    @keyframes drawerIn { from { transform:translateX(-18px); opacity:0; } to { transform:translateX(0); opacity:1; } }\n    @keyframes pageIn { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }\n    @keyframes studyPageIn { from { opacity:0; transform:translateY(5px); } to { opacity:1; transform:translateY(0); } }\n'''
if old_anim not in text:
    raise RuntimeError('page animation css anchor not found')
text = text.replace(old_anim, new_anim, 1)

old_mobile = '''        .choice-card { min-height:145px; padding:1.2rem; }\n'''
new_mobile = '''        .choice-card { height:178px; min-height:178px; padding:1.2rem; }\n'''
if old_mobile not in text:
    raise RuntimeError('mobile choice-card css anchor not found')
text = text.replace(old_mobile, new_mobile, 1)

old_study = '''def study_home():\n    topbar()\n    render_back_button("返回首頁", "home", "back_study_home")\n    st.markdown('<div class="study-header"><div class="eyebrow">STUDY</div><div class="hero-title" style="font-size:2.05rem">你想怎麼學習呢？</div><div class="hero-copy">選擇適合你現在狀態的方式，MedSlime 陪你一起進步。</div></div>', unsafe_allow_html=True)\n    rows = [\n        [("📄", "我有教材", "上傳 PDF 教材，AI 會直接生成 10 題並開始測驗。", "study_material_intro"), ("🧪", "我要刷國考", "練習歷屆國考題目，快速檢測實力與弱點。", "national_exam")],\n        [("📘", "我要複習錯題", "回顧答錯或不確定的題目，加強你的弱點。", "mistakes"), ("⏱️", "我要專心讀書", "用番茄鐘陪你專注，完成每一小段就累積學習時間。", "focus_timer")],\n    ]\n    for row in rows:\n        cols = st.columns(2, gap="large")\n        for col, (icon, title, copy, target) in zip(cols, row):\n            with col:\n                st.markdown(f'<div class="choice-card"><div class="choice-icon-shell"><div class="choice-icon">{icon}</div></div><div class="choice-title">{title}</div><div class="choice-copy">{copy}</div></div>', unsafe_allow_html=True)\n                if target:\n                    st.button(\n                        "進入 →",\n                        key=f"go_{target}",\n                        use_container_width=True,\n                        type="primary",\n                        on_click=set_page_without_extra_rerun,\n                        args=(target,),\n                    )\n                else:\n                    st.button("即將開放", key=f"soon_{title}", use_container_width=True, disabled=True)\n        st.write("")\n'''
new_study = '''def study_home():\n    topbar()\n    render_back_button("返回首頁", "home", "back_study_home")\n    st.markdown('<div class="study-page-transition-anchor"></div>', unsafe_allow_html=True)\n    st.markdown('<div class="study-header"><div class="eyebrow">STUDY</div><div class="hero-title" style="font-size:2.05rem">你想怎麼學習呢？</div><div class="hero-copy">選擇適合你現在狀態的方式，MedSlime 陪你一起進步。</div></div>', unsafe_allow_html=True)\n    rows = [\n        [("📄", "我有教材", "上傳 PDF 教材，AI 會直接生成 10 題並開始測驗。", "study_material_intro"), ("🧪", "我要刷國考", "練習歷屆國考題目，快速檢測實力與弱點。", "national_exam")],\n        [("📘", "我要複習錯題", "回顧答錯或不確定的題目，加強你的弱點。", "mistakes"), ("⏱️", "我要專心讀書", "用番茄鐘陪你專注，完成每一小段就累積學習時間。", "focus_timer")],\n    ]\n    for row_index, row in enumerate(rows):\n        cols = st.columns(2, gap="large")\n        for col_index, (col, (icon, title, copy, target)) in enumerate(zip(cols, row)):\n            with col:\n                with st.container(key=f"study_choice_{row_index}_{col_index}"):\n                    st.markdown(f'<div class="choice-card"><div class="choice-icon-shell"><div class="choice-icon">{icon}</div></div><div class="choice-title">{title}</div><div class="choice-copy">{copy}</div></div>', unsafe_allow_html=True)\n                    if target:\n                        st.button(\n                            "進入 →",\n                            key=f"go_{target}",\n                            use_container_width=True,\n                            type="primary",\n                            on_click=set_page_without_extra_rerun,\n                            args=(target,),\n                        )\n                    else:\n                        st.button("即將開放", key=f"soon_{title}", use_container_width=True, disabled=True)\n'''
if old_study not in text:
    raise RuntimeError('study_home anchor not found')
text = text.replace(old_study, new_study, 1)

path.write_text(text, encoding='utf-8')
print('fixed study layout and page transition')
