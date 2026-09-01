from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

# Session state for pending material processing.
anchor = '    "material_generation_error": None,\n'
insert = '    "material_generation_error": None,\n    "material_pending_bytes": None,\n    "material_pending_name": None,\n    "material_pending_hash": None,\n'
if '"material_pending_bytes"' not in text:
    if anchor not in text:
        raise RuntimeError('default state anchor not found')
    text = text.replace(anchor, insert, 1)

# Mobile spacing: remove stacked large column gaps and use one consistent vertical gap.
mobile_anchor = '        .choice-card { height:178px; min-height:178px; padding:1.2rem; }\n'
mobile_extra = '''        .choice-card { height:178px; min-height:178px; padding:1.2rem; }\n        [class*="st-key-study_choices_grid"] [data-testid="stHorizontalBlock"] { gap:.85rem !important; }\n        [class*="st-key-study_choices_grid"] [data-testid="stColumn"] { margin-bottom:0 !important; }\n        [class*="st-key-study_choice_"] { margin-bottom:0 !important; }\n        [class*="st-key-study_choice_"] [data-testid="stButton"] { margin-top:.55rem !important; margin-bottom:0 !important; }\n'''
if '[class*="st-key-study_choices_grid"] [data-testid="stHorizontalBlock"]' not in text:
    if mobile_anchor not in text:
        raise RuntimeError('mobile spacing anchor not found')
    text = text.replace(mobile_anchor, mobile_extra, 1)

# Wrap the choices in a keyed container so mobile spacing can be scoped safely.
old_rows = '''    for row_index, row in enumerate(rows):\n        cols = st.columns(2, gap="large")\n        for col_index, (col, (icon, title, copy, target)) in enumerate(zip(cols, row)):\n            with col:\n                with st.container(key=f"study_choice_{row_index}_{col_index}"):\n                    st.markdown(f'<div class="choice-card"><div class="choice-icon-shell"><div class="choice-icon">{icon}</div></div><div class="choice-title">{title}</div><div class="choice-copy">{copy}</div></div>', unsafe_allow_html=True)\n                    if target:\n                        st.button(\n                            "進入 →",\n                            key=f"go_{target}",\n                            use_container_width=True,\n                            type="primary",\n                            on_click=set_page_without_extra_rerun,\n                            args=(target,),\n                        )\n                    else:\n                        st.button("即將開放", key=f"soon_{title}", use_container_width=True, disabled=True)\n'''
new_rows = '''    with st.container(key="study_choices_grid"):\n        for row_index, row in enumerate(rows):\n            cols = st.columns(2, gap="large")\n            for col_index, (col, (icon, title, copy, target)) in enumerate(zip(cols, row)):\n                with col:\n                    with st.container(key=f"study_choice_{row_index}_{col_index}"):\n                        st.markdown(f'<div class="choice-card"><div class="choice-icon-shell"><div class="choice-icon">{icon}</div></div><div class="choice-title">{title}</div><div class="choice-copy">{copy}</div></div>', unsafe_allow_html=True)\n                        if target:\n                            st.button(\n                                "進入 →",\n                                key=f"go_{target}",\n                                use_container_width=True,\n                                type="primary",\n                                on_click=set_page_without_extra_rerun,\n                                args=(target,),\n                            )\n                        else:\n                            st.button("即將開放", key=f"soon_{title}", use_container_width=True, disabled=True)\n'''
if 'key="study_choices_grid"' not in text:
    if old_rows not in text:
        raise RuntimeError('study choices block not found')
    text = text.replace(old_rows, new_rows, 1)

# Replace inline processing in the main material intro page with a queued processing page.
start = text.index('def study_material_intro():')
end = text.index('\ndef study_material_upload():', start)
old_intro = text[start:end]
new_intro = '''def _queue_material_processing(uploaded):\n    file_bytes = uploaded.getvalue()\n    file_hash = hashlib.sha256(file_bytes).hexdigest()\n    if st.session_state.material_file_hash == file_hash and st.session_state.material_questions and len(st.session_state.material_questions) == QUIZ_SIZE:\n        clear_quiz_answers()\n        st.session_state.medslime_page = "quiz"\n        st.session_state.menu_open = False\n        st.rerun()\n    st.session_state.uploaded_learning_file = uploaded.name\n    st.session_state.material_pending_bytes = file_bytes\n    st.session_state.material_pending_name = uploaded.name\n    st.session_state.material_pending_hash = file_hash\n    st.session_state.material_generation_error = None\n    st.session_state.medslime_page = "material_processing"\n    st.session_state.menu_open = False\n    st.rerun()\n\n\ndef study_material_intro():\n    topbar()\n    render_back_button("返回學習", "study", "intro_back")\n    with st.container(key="material_intro_card"):\n        st.markdown('<div class="intro-art"><div class="mini-slime"><div class="mini-shine"></div><div class="mini-mouth"></div></div><div class="book-stack">📚</div></div><div class="hero-title material-intro-title">上傳教材，AI 生成 10 題<br>開始你的專屬測驗。</div><div class="hero-copy" style="max-width:680px;margin:.8rem auto 0">選好 PDF 後，MedSlime 會直接讀取教材；完成後自動帶你進入第 1 題。</div>', unsafe_allow_html=True)\n        with st.container(key="material_intro_uploader"):\n            uploaded = st.file_uploader("上傳教材開始學習", type=["pdf"], key="medslime_material_pdf_intro", label_visibility="collapsed")\n\n    if uploaded is None:\n        if st.session_state.material_generation_error:\n            st.error(st.session_state.material_generation_error)\n        return\n    _queue_material_processing(uploaded)\n\n\ndef material_processing_page():\n    topbar()\n    filename = st.session_state.material_pending_name or st.session_state.uploaded_learning_file or "教材.pdf"\n    file_bytes = st.session_state.material_pending_bytes\n    file_hash = st.session_state.material_pending_hash\n\n    # The loading card is rendered first at the top of its own page, then Streamlit\n    # continues with the slower PDF parsing / AI request below.\n    render_loading_card(filename)\n\n    if not file_bytes or not file_hash:\n        st.session_state.material_generation_error = "找不到待處理的教材，請重新上傳。"\n        st.session_state.medslime_page = "study_material_intro"\n        st.rerun()\n\n    try:\n        _, pages = extract_pdf_text(file_bytes)\n        document_text = build_document_text(pages)\n        if len(document_text.strip()) < 250:\n            raise ValueError("這份 PDF 可讀取的文字太少，可能是掃描檔或圖片型 PDF。")\n        payload = generate_material_quiz(document_text)\n        st.session_state.material_file_hash = file_hash\n        st.session_state.material_subject = payload.get("subject") or "教材測驗"\n        st.session_state.material_questions = payload["questions"]\n        clear_quiz_answers()\n        st.session_state.material_generation_error = None\n        st.session_state.material_pending_bytes = None\n        st.session_state.material_pending_name = None\n        st.session_state.material_pending_hash = None\n        st.session_state.medslime_page = "quiz"\n        st.session_state.menu_open = False\n        st.rerun()\n    except Exception as error:\n        st.session_state.material_generation_error = f"{type(error).__name__}: {error}"\n        st.session_state.material_pending_bytes = None\n        st.session_state.material_pending_name = None\n        st.session_state.material_pending_hash = None\n        st.session_state.medslime_page = "study_material_intro"\n        st.rerun()\n\n'''
text = text[:start] + new_intro + text[end:]

# Route legacy upload page through the same processing screen too.
old_upload_processing = '''    file_bytes = uploaded.getvalue()\n    file_hash = hashlib.sha256(file_bytes).hexdigest()\n\n    if st.session_state.material_file_hash == file_hash and st.session_state.material_questions and len(st.session_state.material_questions) == QUIZ_SIZE:\n        clear_quiz_answers()\n        goto("quiz")\n\n    st.session_state.uploaded_learning_file = uploaded.name\n    st.session_state.material_generation_error = None\n    loading = st.empty()\n    with loading.container():\n        render_loading_card(uploaded.name)\n\n    try:\n        _, pages = extract_pdf_text(file_bytes)\n        document_text = build_document_text(pages)\n        if len(document_text.strip()) < 250:\n            raise ValueError("這份 PDF 可讀取的文字太少，可能是掃描檔或圖片型 PDF。")\n        payload = generate_material_quiz(document_text)\n        st.session_state.material_file_hash = file_hash\n        st.session_state.material_subject = payload.get("subject") or "教材測驗"\n        st.session_state.material_questions = payload["questions"]\n        clear_quiz_answers()\n        st.session_state.material_generation_error = None\n        loading.empty()\n        goto("quiz")\n    except Exception as error:\n        loading.empty()\n        st.session_state.material_generation_error = f"{type(error).__name__}: {error}"\n        st.error("教材處理失敗，請重新上傳或稍後再試。")\n        with st.expander("查看錯誤資訊"):\n            st.code(st.session_state.material_generation_error)\n'''
if old_upload_processing in text:
    text = text.replace(old_upload_processing, '    _queue_material_processing(uploaded)\n', 1)

# Add router entry.
router_anchor = 'elif page == "study_material_upload":\n    study_material_upload()\n'
router_new = 'elif page == "study_material_upload":\n    study_material_upload()\nelif page == "material_processing":\n    material_processing_page()\n'
if 'elif page == "material_processing":' not in text:
    if router_anchor not in text:
        raise RuntimeError('router anchor not found')
    text = text.replace(router_anchor, router_new, 1)

path.write_text(text, encoding='utf-8')
print('fixed mobile study spacing and moved material processing to dedicated page')
