from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

replacements = [
    (
        '''def national_exam_quiz_page():\n    questions = st.session_state.national_exam_questions or []\n    if not questions:\n        goto("national_exam")\n\n    topbar()\n''',
        '''def national_exam_quiz_page():\n    questions = st.session_state.national_exam_questions or []\n    if not questions:\n        goto("national_exam")\n\n    topbar()\n    render_back_button("返回國考", "national_exam", "back_national_exam_quiz")\n''',
        'national exam quiz',
    ),
    (
        '''def national_exam_result_page():\n    questions = st.session_state.national_exam_questions or []\n    if not questions:\n        goto("national_exam")\n    topbar()\n''',
        '''def national_exam_result_page():\n    questions = st.session_state.national_exam_questions or []\n    if not questions:\n        goto("national_exam")\n    topbar()\n    render_back_button("返回國考", "national_exam", "back_national_exam_result")\n''',
        'national exam result',
    ),
    (
        '''def material_quiz_page():\n    questions = st.session_state.material_questions or []\n    if len(questions) != QUIZ_SIZE:\n        goto("study_material_upload")\n\n    topbar()\n''',
        '''def material_quiz_page():\n    questions = st.session_state.material_questions or []\n    if len(questions) != QUIZ_SIZE:\n        goto("study_material_upload")\n\n    topbar()\n    render_back_button("返回教材", "study_material_intro", "back_material_quiz")\n''',
        'material quiz',
    ),
    (
        '''def material_quiz_result():\n    questions = st.session_state.material_questions or []\n    if len(questions) != QUIZ_SIZE:\n        goto("study_material_intro")\n\n    topbar()\n''',
        '''def material_quiz_result():\n    questions = st.session_state.material_questions or []\n    if len(questions) != QUIZ_SIZE:\n        goto("study_material_intro")\n\n    topbar()\n    render_back_button("返回教材", "study_material_intro", "back_material_result")\n''',
        'material result',
    ),
]

for old, new, label in replacements:
    if new in text:
        continue
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 match, got {count}')
    text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
print('remaining back buttons patched')
