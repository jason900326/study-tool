from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

anchor = '''def load_national_exam_paper(exam_year, exam_round, subject):\n'''
helper = r'''@st.cache_data(ttl=86400, show_spinner=False)
def _load_official_answer_key(answer_pdf_url):
    """Read the official MOEX answer sheet and return {1: 'A', ..., 80: 'D'}."""
    raw_url = str(answer_pdf_url or "").strip()
    if not raw_url:
        return {}

    pdf_bytes = _download_pdf_for_viewer(raw_url)
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        pdf_text = "\n".join(document.load_page(i).get_text("text") for i in range(document.page_count))
    finally:
        document.close()

    normalized = pdf_text.translate(str.maketrans({"Ａ": "A", "Ｂ": "B", "Ｃ": "C", "Ｄ": "D"}))
    if "標準答案" in normalized:
        normalized = normalized.split("標準答案", 1)[1]
    if "備" in normalized:
        normalized = normalized.split("備", 1)[0]

    answers = re.findall(r"(?<![A-Za-z])[ABCD](?![A-Za-z])", normalized.upper())
    if len(answers) < 80:
        # Some PDF extractors place the answer letters on lines after the 答案 label.
        answer_lines = []
        lines = pdf_text.translate(str.maketrans({"Ａ": "A", "Ｂ": "B", "Ｃ": "C", "Ｄ": "D"})).splitlines()
        collecting = False
        for line in lines:
            if "標準答案" in line:
                collecting = True
                continue
            if collecting and "備" in line:
                break
            if collecting:
                answer_lines.extend(re.findall(r"(?<![A-Za-z])[ABCD](?![A-Za-z])", line.upper()))
        answers = answer_lines

    if len(answers) < 80:
        return {}
    return {number: answers[number - 1] for number in range(1, 81)}


'''
if '_load_official_answer_key' not in text:
    if anchor not in text:
        raise RuntimeError('load_national_exam_paper anchor not found')
    text = text.replace(anchor, helper + anchor, 1)

old_select = '''            "correct_answers, source_page_url, question_pdf_url, has_image_hint, parse_status"\n'''
new_select = '''            "correct_answers, source_page_url, question_pdf_url, answer_pdf_url, corrected_answer_pdf_url, "\n            "has_image_hint, parse_status"\n'''
if old_select not in text:
    raise RuntimeError('national exam select anchor not found')
text = text.replace(old_select, new_select, 1)

old_loop = '''    for row in rows:\n        options = list(row.get("options") or [])\n        correct_answers = row.get("correct_answers") or []\n        has_image_hint = bool(row.get("has_image_hint"))\n        valid_answer = len(correct_answers) == 1 and correct_answers[0] in answer_map\n        image_choice_mode = False\n        reason = None\n\n        # A valid official A-D answer is mandatory for every interactive question.\n        if not valid_answer:\n            reason = "多答案或答案格式特殊"\n        elif has_image_hint:\n            # Image questions are allowed even when the parser cannot reconstruct\n            # all four option texts. In that case, show the original PDF question\n            # inline and let the learner answer with A / B / C / D.\n            if row.get("parse_status") != "ok" or len(options) != 4:\n                options = ["A", "B", "C", "D"]\n                image_choice_mode = True\n        elif row.get("parse_status") != "ok":\n            reason = "解析異常"\n        elif len(options) != 4:\n            reason = "選項不完整"\n\n        if reason:\n            excluded.append({"question_number": row.get("question_number"), "reason": reason})\n            continue\n\n        number = row.get("question_number")\n        usable.append({\n            "question": row.get("question") or "",\n            "options": options,\n            "correct_index": answer_map[correct_answers[0]],\n'''
new_loop = '''    official_answer_cache = {}\n\n    for row in rows:\n        number = row.get("question_number")\n        options = list(row.get("options") or [])\n        correct_answers = list(row.get("correct_answers") or [])\n        has_image_hint = bool(row.get("has_image_hint"))\n        source_only_mode = (\n            row.get("parse_status") != "ok"\n            or len(options) != 4\n            or any(not str(option or "").strip() for option in options)\n        )\n\n        valid_answer = len(correct_answers) == 1 and correct_answers[0] in answer_map\n        if not valid_answer:\n            answer_url = row.get("corrected_answer_pdf_url") or row.get("answer_pdf_url")\n            if answer_url not in official_answer_cache:\n                try:\n                    official_answer_cache[answer_url] = _load_official_answer_key(answer_url)\n                except Exception:\n                    official_answer_cache[answer_url] = {}\n            repaired_answer = official_answer_cache.get(answer_url, {}).get(int(number or 0))\n            if repaired_answer in answer_map:\n                correct_answers = [repaired_answer]\n                valid_answer = True\n\n        if not valid_answer:\n            excluded.append({"question_number": number, "reason": "官方答案讀取失敗"})\n            continue\n\n        if source_only_mode:\n            options = ["A", "B", "C", "D"]\n\n        question_text = str(row.get("question") or "").strip()\n        if not question_text:\n            question_text = f"官方第 {number} 題（題目內容請查看官方原題）"\n\n        usable.append({\n            "question": question_text,\n            "options": options,\n            "correct_index": answer_map[correct_answers[0]],\n'''
if old_loop not in text:
    raise RuntimeError('current national exam loader loop not found')
text = text.replace(old_loop, new_loop, 1)

text = text.replace('''            "image_choice_mode": image_choice_mode,\n''', '''            "image_choice_mode": source_only_mode,\n            "source_only_mode": source_only_mode,\n''', 1)

path.write_text(text, encoding='utf-8')
print('updated national exam loader to repair answers from official MOEX sheets and keep all rows')
