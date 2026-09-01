from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

# ---- session state ----
text = text.replace('''    "national_exam_load_error": None,\n''', '''    "national_exam_load_error": None,\n    "national_exam_started_at": None,\n    "national_exam_elapsed_seconds": None,\n    "national_exam_struck": {},\n''', 1)
text = text.replace('''    "quiz_finish_pending": False,\n''', '''    "quiz_finish_pending": False,\n    "material_quiz_started_at": None,\n    "material_quiz_elapsed_seconds": None,\n    "material_quiz_struck": {},\n''', 1)

# ---- helpers ----
anchor = '# =========================================================\n# Style\n# =========================================================\n'
helper = r'''
def _format_quiz_elapsed(seconds):
    seconds = max(0, int(seconds or 0))
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours} 小時 {minutes} 分 {secs} 秒"
    if minutes:
        return f"{minutes} 分 {secs} 秒"
    return f"{secs} 秒"


def _render_strikeable_options(prefix, index, options, answer_store, struck_store):
    struck = set(struck_store.get(index, []))
    selected_index = answer_store.get(index)
    for option_index, option in enumerate(options):
        circle_col, text_col = st.columns([0.075, 0.925], gap="small")
        with circle_col:
            circle = "●" if selected_index == option_index else "○"
            if st.button(circle, key=f"{prefix}_pick_{index}_{option_index}", help="選擇這個答案"):
                answer_store[index] = option_index
                st.rerun()
        with text_col:
            is_struck = option_index in struck
            key_state = "on" if is_struck else "off"
            label = normalize_scientific_notation(option)
            if st.button(label, key=f"{prefix}_strike_{key_state}_{index}_{option_index}", use_container_width=True, help="劃掉 / 取消劃掉這個選項"):
                if is_struck:
                    struck.discard(option_index)
                else:
                    struck.add(option_index)
                struck_store[index] = sorted(struck)
                st.rerun()


'''
if '_render_strikeable_options' not in text:
    text = text.replace(anchor, helper + anchor, 1)

# ---- CSS ----
css_anchor = '''    [data-testid="stRadio"] [role="radiogroup"] { gap:.5rem; }\n'''
css_add = '''    [class*="st-key-national_strike_on_"] button p,\n    [class*="st-key-material_strike_on_"] button p { text-decoration:line-through !important; opacity:.42 !important; }\n    [class*="st-key-national_strike_"] button,\n    [class*="st-key-material_strike_"] button { justify-content:flex-start !important; text-align:left !important; background:rgba(255,255,255,.82) !important; color:#244c39 !important; border:1px solid #e0ebe5 !important; box-shadow:none !important; }\n    [class*="st-key-national_pick_"] button,\n    [class*="st-key-material_pick_"] button { min-width:38px !important; width:38px !important; padding:0 !important; border:none !important; background:transparent !important; box-shadow:none !important; font-size:1.15rem !important; }\n    .quiz-result-stats { display:flex; gap:.65rem; flex-wrap:wrap; margin:.9rem 0 1.25rem; }\n    .quiz-result-stat { background:#fff; border:1px solid #dceae2; border-radius:16px; padding:.75rem 1rem; color:#315b47; font-weight:800; }\n    .quiz-result-stat strong { color:#173b2b; font-size:1.18rem; }\n'''
if css_add not in text:
    text = text.replace(css_anchor, css_add + css_anchor, 1)

# ---- clear state ----
text = text.replace('''    st.session_state.national_exam_uncertain = {}\n    st.session_state.national_exam_mistakes_saved = False\n''', '''    st.session_state.national_exam_uncertain = {}\n    st.session_state.national_exam_struck = {}\n    st.session_state.national_exam_elapsed_seconds = None\n    st.session_state.national_exam_mistakes_saved = False\n''', 1)
text = text.replace('''    st.session_state.quiz_uncertain = {}\n''', '''    st.session_state.quiz_uncertain = {}\n    st.session_state.material_quiz_struck = {}\n    st.session_state.material_quiz_elapsed_seconds = None\n''', 1)

# ---- start timers ----
text = text.replace('''    clear_national_exam_answers()\n    st.session_state.medslime_page = "national_exam_quiz"\n''', '''    clear_national_exam_answers()\n    st.session_state.national_exam_started_at = time.time()\n    st.session_state.medslime_page = "national_exam_quiz"\n''', 1)
text = text.replace('''        st.session_state.material_questions = payload["questions"]\n        clear_quiz_answers()\n''', '''        st.session_state.material_questions = payload["questions"]\n        clear_quiz_answers()\n        st.session_state.material_quiz_started_at = time.time()\n''', 1)

# ---- save functions stop depending on old radio ----
old = '''def save_current_national_exam_state(index, options):\n    answer_key = f"exam_answer_{index}"\n    uncertain_key = f"exam_uncertain_{index}"\n    selected = st.session_state.get(answer_key)\n    if selected in options:\n        st.session_state.national_exam_answers[index] = options.index(selected)\n    else:\n        st.session_state.national_exam_answers.pop(index, None)\n    st.session_state.national_exam_uncertain[index] = bool(st.session_state.get(uncertain_key, False))\n'''
new = '''def save_current_national_exam_state(index, options):\n    uncertain_key = f"exam_uncertain_{index}"\n    st.session_state.national_exam_uncertain[index] = bool(st.session_state.get(uncertain_key, False))\n'''
text = text.replace(old, new, 1)

old = '''def save_current_quiz_state(index, options):\n    answer_key = f"material_answer_{index}"\n    uncertain_key = f"material_uncertain_{index}"\n    selected = st.session_state.get(answer_key)\n    if selected in options:\n        st.session_state.quiz_answers[index] = options.index(selected)\n    else:\n        st.session_state.quiz_answers.pop(index, None)\n    st.session_state.quiz_uncertain[index] = bool(st.session_state.get(uncertain_key, False))\n'''
new = '''def save_current_quiz_state(index, options):\n    uncertain_key = f"material_uncertain_{index}"\n    st.session_state.quiz_uncertain[index] = bool(st.session_state.get(uncertain_key, False))\n'''
text = text.replace(old, new, 1)

# ---- replace national radio ----
old = '''    selected = st.radio("選擇答案", options, index=None, key=answer_key, label_visibility="collapsed", format_func=normalize_scientific_notation)\n    uncertain = st.checkbox("❓ 我不確定這個觀念", key=uncertain_key)\n    if selected in options:\n        st.session_state.national_exam_answers[index] = options.index(selected)\n    else:\n        st.session_state.national_exam_answers.pop(index, None)\n    st.session_state.national_exam_uncertain[index] = bool(uncertain)\n'''
new = '''    _render_strikeable_options("national", index, options, st.session_state.national_exam_answers, st.session_state.national_exam_struck)\n    uncertain = st.checkbox("❓ 我不確定這個觀念", key=uncertain_key)\n    st.session_state.national_exam_uncertain[index] = bool(uncertain)\n'''
text = text.replace(old, new, 1)

# ---- replace material radio ----
old = '''    selected = st.radio("選擇答案", options, index=None, key=answer_key, label_visibility="collapsed", format_func=normalize_scientific_notation)\n    uncertain = st.checkbox("❓ 我不確定這個觀念", key=uncertain_key)\n\n    if selected in options:\n        st.session_state.quiz_answers[index] = options.index(selected)\n    else:\n        st.session_state.quiz_answers.pop(index, None)\n    st.session_state.quiz_uncertain[index] = bool(uncertain)\n'''
new = '''    _render_strikeable_options("material", index, options, st.session_state.quiz_answers, st.session_state.material_quiz_struck)\n    uncertain = st.checkbox("❓ 我不確定這個觀念", key=uncertain_key)\n    st.session_state.quiz_uncertain[index] = bool(uncertain)\n'''
text = text.replace(old, new, 1)

# ---- remove yellow sync warnings ----
text = text.replace('''    except Exception:\n        st.warning("這次錯題暫時無法同步到錯題庫，但測驗結果仍可正常查看。")\n''', '''    except Exception:\n        pass\n''')

# ---- result score/time national ----
old = '''    subtitle = f'{roc_year_label(meta.get("exam_year", 2026))} · {meta.get("exam_round", "")} · {html.escape(str(meta.get("subject", "")))}'\n    st.markdown(f'<div class="study-header"><div class="eyebrow">RESULT</div><div class="hero-title" style="font-size:2.05rem">完成國考練習</div><div class="hero-copy">{subtitle}<br>真正掌握 {correct} / {len(questions)} 題。</div></div>', unsafe_allow_html=True)\n'''
new = '''    if st.session_state.national_exam_elapsed_seconds is None:\n        started_at = st.session_state.national_exam_started_at or time.time()\n        st.session_state.national_exam_elapsed_seconds = max(0, int(time.time() - started_at))\n    score = round((correct / len(questions)) * 100) if questions else 0\n    elapsed_label = _format_quiz_elapsed(st.session_state.national_exam_elapsed_seconds)\n    subtitle = f'{roc_year_label(meta.get("exam_year", 2026))} · {meta.get("exam_round", "")} · {html.escape(str(meta.get("subject", "")))}'\n    st.markdown(f'<div class="study-header"><div class="eyebrow">RESULT</div><div class="hero-title" style="font-size:2.05rem">完成國考練習</div><div class="hero-copy">{subtitle}<br>真正掌握 {correct} / {len(questions)} 題。</div></div><div class="quiz-result-stats"><div class="quiz-result-stat">分數<br><strong>{score} / 100</strong></div><div class="quiz-result-stat">作答時間<br><strong>{elapsed_label}</strong></div></div>', unsafe_allow_html=True)\n'''
text = text.replace(old, new, 1)

# ---- result score/time material ----
old = '''    st.markdown(f'<div class="study-header"><div class="eyebrow">RESULT</div><div class="hero-title" style="font-size:2.05rem">完成 {QUIZ_SIZE} 題測驗</div><div class="hero-copy">真正掌握 {correct} / {QUIZ_SIZE} 題。答對但標記 ❓ 的題目仍會列入複習。</div></div>', unsafe_allow_html=True)\n'''
new = '''    if st.session_state.material_quiz_elapsed_seconds is None:\n        started_at = st.session_state.material_quiz_started_at or time.time()\n        st.session_state.material_quiz_elapsed_seconds = max(0, int(time.time() - started_at))\n    score = round((correct / QUIZ_SIZE) * 100) if QUIZ_SIZE else 0\n    elapsed_label = _format_quiz_elapsed(st.session_state.material_quiz_elapsed_seconds)\n    st.markdown(f'<div class="study-header"><div class="eyebrow">RESULT</div><div class="hero-title" style="font-size:2.05rem">完成 {QUIZ_SIZE} 題測驗</div><div class="hero-copy">真正掌握 {correct} / {QUIZ_SIZE} 題。答對但標記 ❓ 的題目仍會列入複習。</div></div><div class="quiz-result-stats"><div class="quiz-result-stat">分數<br><strong>{score} / 100</strong></div><div class="quiz-result-stat">作答時間<br><strong>{elapsed_label}</strong></div></div>', unsafe_allow_html=True)\n'''
text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
print('fast quiz UX patch applied')
