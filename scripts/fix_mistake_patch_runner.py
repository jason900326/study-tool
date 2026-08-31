from pathlib import Path

path = Path("scripts/build_mistake_bank.py")
text = path.read_text(encoding="utf-8")

old = '''# Reset the per-attempt save guards whenever a new attempt starts.\nmaterial_reset_anchor = "    st.session_state.quiz_finish_pending = False\\n"\nmaterial_reset_new = material_reset_anchor + "    st.session_state.material_mistakes_saved = False\\n"\nif "    st.session_state.material_mistakes_saved = False\\n" not in text[text.find("def clear_quiz_answers"):text.find("def prepare_material_upload")]:\n    replace_once(material_reset_anchor, material_reset_new, "material mistake reset")\n\nnational_reset_anchor = "    st.session_state.national_exam_uncertain = {}\\n"\nnational_reset_new = national_reset_anchor + "    st.session_state.national_exam_mistakes_saved = False\\n"\nif national_reset_new not in text:\n    replace_once(national_reset_anchor, national_reset_new, "national mistake reset")\n'''

new = '''# Reset the per-attempt save guards whenever a new attempt starts.\nmaterial_reset_anchor = "    st.session_state.quiz_finish_pending = False\\n"\nmaterial_reset_new = material_reset_anchor + "    st.session_state.material_mistakes_saved = False\\n"\nmaterial_start = text.find("def clear_quiz_answers():")\nmaterial_end = text.find("def prepare_material_upload():")\nmaterial_block = text[material_start:material_end]\nif "    st.session_state.material_mistakes_saved = False\\n" not in material_block:\n    if material_reset_anchor not in material_block:\n        raise RuntimeError("material mistake reset anchor not found in clear_quiz_answers")\n    material_block = material_block.replace(material_reset_anchor, material_reset_new, 1)\n    text = text[:material_start] + material_block + text[material_end:]\n\nnational_reset_anchor = "    st.session_state.national_exam_uncertain = {}\\n"\nnational_reset_new = national_reset_anchor + "    st.session_state.national_exam_mistakes_saved = False\\n"\nnational_start = text.find("def clear_national_exam_answers():")\nnational_end = text.find("def start_national_exam_quiz")\nnational_block = text[national_start:national_end]\nif "    st.session_state.national_exam_mistakes_saved = False\\n" not in national_block:\n    if national_reset_anchor not in national_block:\n        raise RuntimeError("national mistake reset anchor not found in clear_national_exam_answers")\n    national_block = national_block.replace(national_reset_anchor, national_reset_new, 1)\n    text = text[:national_start] + national_block + text[national_end:]\n'''

if old not in text:
    raise RuntimeError("target reset block not found in build_mistake_bank.py")
text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("scoped mistake reset patch")
