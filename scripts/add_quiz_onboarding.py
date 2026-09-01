from pathlib import Path

path = Path("streamlit_app.py")
text = path.read_text(encoding="utf-8")

if "def _render_quiz_onboarding():" in text:
    raise SystemExit(0)

state_anchor = '    "material_quiz_struck": {},\n'
state_replacement = state_anchor + '    "quiz_onboarding_seen": False,\n    "quiz_onboarding_started_at": None,\n'
if state_anchor not in text:
    raise SystemExit("DEFAULT_STATE anchor not found")
text = text.replace(state_anchor, state_replacement, 1)

function_anchor = '''def _render_uncertain_toggle(prefix, index, uncertain_store):
'''
function_insert = '''def _render_quiz_onboarding():
    if st.session_state.quiz_onboarding_seen:
        return True

    if st.session_state.quiz_onboarding_started_at is None:
        st.session_state.quiz_onboarding_started_at = time.time()

    st.markdown(
        """
        <div class="quiz-onboarding-card">
            <div class="quiz-onboarding-kicker">第一次作答？</div>
            <div class="quiz-onboarding-title">三個操作就夠了</div>
            <div class="quiz-onboarding-list">
                <div class="quiz-onboarding-row"><span class="quiz-onboarding-icon">○</span><div><b>點圓圈</b><small>選擇正式答案</small></div></div>
                <div class="quiz-onboarding-row"><span class="quiz-onboarding-icon quiz-onboarding-text-icon">Aa</span><div><b>點選項文字</b><small>劃掉／取消劃掉選項</small></div></div>
                <div class="quiz-onboarding-row"><span class="quiz-onboarding-icon">❓</span><div><b>我不確定</b><small>答案照樣保留，同時標記這題不熟</small></div></div>
            </div>
            <div class="quiz-onboarding-note">之後不會再自動顯示這個教學。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("知道了，開始作答", type="primary", use_container_width=True, key="quiz_onboarding_start"):
        started = st.session_state.quiz_onboarding_started_at
        if started is not None:
            onboarding_seconds = max(0.0, time.time() - started)
            for timer_key in ("material_quiz_started_at", "national_exam_started_at"):
                timer_value = st.session_state.get(timer_key)
                if timer_value is not None:
                    st.session_state[timer_key] = timer_value + onboarding_seconds
        st.session_state.quiz_onboarding_seen = True
        st.session_state.quiz_onboarding_started_at = None
        st.rerun()
    return False


'''
if function_anchor not in text:
    raise SystemExit("Onboarding function anchor not found")
text = text.replace(function_anchor, function_insert + function_anchor, 1)

css_anchor = '''    .quiz-result-stats { display:flex; gap:.65rem; flex-wrap:wrap; margin:.9rem 0 1.25rem; }
'''
css_insert = '''    .quiz-onboarding-card {
        margin:.55rem 0 .7rem; padding:1rem 1.05rem; border:1px solid #d9e9df; border-radius:18px;
        background:linear-gradient(145deg,#fbfffc,#f0f8f3); box-shadow:0 8px 24px rgba(44,91,67,.08); color:#244c39;
    }
    .quiz-onboarding-kicker { font-size:.76rem; font-weight:900; color:#6b8f7c; letter-spacing:.04em; margin-bottom:.15rem; }
    .quiz-onboarding-title { font-size:1.12rem; font-weight:900; margin-bottom:.75rem; }
    .quiz-onboarding-list { display:flex; flex-direction:column; gap:.58rem; }
    .quiz-onboarding-row { display:flex; align-items:center; gap:.72rem; }
    .quiz-onboarding-icon {
        width:36px; height:36px; min-width:36px; display:flex; align-items:center; justify-content:center;
        border:1px solid #cddfd4; border-radius:50%; background:#fff; color:#17212a; font-size:1.15rem; font-weight:900;
    }
    .quiz-onboarding-text-icon { font-size:.8rem; letter-spacing:-.03em; }
    .quiz-onboarding-row b { display:block; font-size:1rem; line-height:1.25; }
    .quiz-onboarding-row small { display:block; margin-top:.08rem; color:#668174; font-size:.84rem; line-height:1.35; }
    .quiz-onboarding-note { margin-top:.75rem; padding-top:.65rem; border-top:1px solid #dfebe4; color:#82968b; font-size:.75rem; }
    @media (max-width:700px) {
        .quiz-onboarding-card { padding:.9rem; border-radius:16px; }
        .quiz-onboarding-title { font-size:1.06rem; }
        .quiz-onboarding-row b { font-size:1rem; }
        .quiz-onboarding-row small { font-size:.8rem; }
    }

'''
if css_anchor not in text:
    raise SystemExit("CSS anchor not found")
text = text.replace(css_anchor, css_insert + css_anchor, 1)

national_anchor = '''    _render_strikeable_options("national", index, options, st.session_state.national_exam_answers, st.session_state.national_exam_struck)
'''
material_anchor = '''    _render_strikeable_options("material", index, options, st.session_state.quiz_answers, st.session_state.material_quiz_struck)
'''
if national_anchor not in text or material_anchor not in text:
    raise SystemExit("Quiz render anchor not found")
text = text.replace(national_anchor, '    if not _render_quiz_onboarding():\n        return\n\n' + national_anchor, 1)
text = text.replace(material_anchor, '    if not _render_quiz_onboarding():\n        return\n\n' + material_anchor, 1)

path.write_text(text, encoding="utf-8")
