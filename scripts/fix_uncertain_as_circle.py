from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

# Add a real uncertainty row using the same geometry as answer options.
anchor = '''def _render_strikeable_options(prefix, index, options, answer_store, struck_store):\n'''
helper = '''def _render_uncertain_toggle(prefix, index, uncertain_store):\n    is_uncertain = bool(uncertain_store.get(index, False))\n    circle_col, text_col = st.columns([0.09, 0.91], gap="small")\n    with circle_col:\n        circle = "●" if is_uncertain else "○"\n        with st.container(key=f"{prefix}_uncertain_pick_wrap_{index}"):\n            if st.button(circle, key=f"{prefix}_uncertain_pick_{index}"):\n                uncertain_store[index] = not is_uncertain\n                st.rerun()\n    with text_col:\n        with st.container(key=f"{prefix}_uncertain_text_{index}"):\n            st.markdown('<div class="uncertain-inline-text"><span>❓</span> 我不確定</div>', unsafe_allow_html=True)\n\n\n'''
if helper not in text:
    if anchor not in text:
        raise RuntimeError('option helper anchor not found')
    text = text.replace(anchor, helper + anchor, 1)

# Remove dependency on checkbox widget state when navigating.
old = '''def save_current_national_exam_state(index, options):\n    uncertain_key = f"exam_uncertain_{index}"\n    st.session_state.national_exam_uncertain[index] = bool(st.session_state.get(uncertain_key, False))\n'''
new = '''def save_current_national_exam_state(index, options):\n    # Answer and uncertainty are saved immediately by their custom controls.\n    return\n'''
if old in text:
    text = text.replace(old, new, 1)

old = '''def save_current_quiz_state(index, options):\n    uncertain_key = f"material_uncertain_{index}"\n    st.session_state.quiz_uncertain[index] = bool(st.session_state.get(uncertain_key, False))\n'''
new = '''def save_current_quiz_state(index, options):\n    # Answer and uncertainty are saved immediately by their custom controls.\n    return\n'''
if old in text:
    text = text.replace(old, new, 1)

# Replace checkbox rendering in national exam and material quizzes.
national_old = '''    uncertain = st.checkbox("❓ 我不確定", key=uncertain_key)\n    st.session_state.national_exam_uncertain[index] = bool(uncertain)\n'''
national_new = '''    _render_uncertain_toggle("national", index, st.session_state.national_exam_uncertain)\n'''
if national_old not in text:
    raise RuntimeError('national uncertainty checkbox not found')
text = text.replace(national_old, national_new, 1)

material_old = '''    uncertain = st.checkbox("❓ 我不確定", key=uncertain_key)\n    st.session_state.quiz_uncertain[index] = bool(uncertain)\n'''
material_new = '''    _render_uncertain_toggle("material", index, st.session_state.quiz_uncertain)\n'''
if material_old not in text:
    raise RuntimeError('material uncertainty checkbox not found')
text = text.replace(material_old, material_new, 1)

# Style the uncertainty row using the same circle sizing / alignment as answer rows.
css_anchor = '''    .quiz-result-stats { display:flex; gap:.65rem; flex-wrap:wrap; margin:.9rem 0 1.25rem; }\n'''
css = '''    [class*="st-key-national_uncertain_pick_wrap_"] button,\n    [class*="st-key-material_uncertain_pick_wrap_"] button {\n        display:flex !important; align-items:center !important; justify-content:center !important;\n        min-width:38px !important; width:38px !important; min-height:38px !important; height:38px !important;\n        padding:0 !important; margin:0 auto !important; border:none !important; background:transparent !important;\n        color:#17212a !important; box-shadow:none !important; font-size:1.2rem !important;\n    }\n    [class*="st-key-national_uncertain_pick_wrap_"] button p,\n    [class*="st-key-material_uncertain_pick_wrap_"] button p {\n        color:#17212a !important; opacity:1 !important; font-size:1.2rem !important; line-height:1 !important; margin:0 !important;\n    }\n    [class*="st-key-national_uncertain_text_"] ,\n    [class*="st-key-material_uncertain_text_"] { min-height:38px !important; display:flex !important; align-items:center !important; }\n    .uncertain-inline-text {\n        min-height:38px; display:flex; align-items:center; gap:.35rem; padding:.45rem .15rem;\n        color:#244c39; line-height:1.45;\n    }\n'''
if css not in text:
    if css_anchor not in text:
        raise RuntimeError('result stats css anchor not found')
    text = text.replace(css_anchor, css + css_anchor, 1)

path.write_text(text, encoding='utf-8')
print('uncertainty control now uses real circle row')
