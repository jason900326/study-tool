from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

old = '''    if len(answers) != 80:\n        # Defensive fallback: only inspect the 標準答案 -> 備註 section.\n        section = normalized\n        if "標準答案：" in section:\n            section = section.split("標準答案：", 1)[1]\n        if "備" in section:\n            section = section.split("備", 1)[0]\n        answers = re.findall(r"(?<![A-Za-z])[ABCD](?![A-Za-z])", section.upper())\n\n    if len(answers) != 80:\n        return {}\n    return {number: answers[number - 1] for number in range(1, 81)}\n'''
new = '''    if len(answers) != 80:\n        # Defensive fallback: only inspect the 標準答案 -> 備註 section.\n        section = normalized\n        if "標準答案：" in section:\n            section = section.split("標準答案：", 1)[1]\n        if "備" in section:\n            section = section.split("備", 1)[0]\n        answers = re.findall(r"(?<![A-Za-z])[ABCD](?![A-Za-z])", section.upper())\n\n    if len(answers) != 80:\n        # PyMuPDF can split the visual answer rows differently from plain text.\n        # Read individual word tokens; MOEX answer sheets expose the 80 answers\n        # as standalone full-width/ASCII A-D tokens.\n        document = fitz.open(stream=pdf_bytes, filetype="pdf")\n        try:\n            token_answers = []\n            translate = str.maketrans({"Ａ": "A", "Ｂ": "B", "Ｃ": "C", "Ｄ": "D"})\n            for page_index in range(document.page_count):\n                page = document.load_page(page_index)\n                for word in page.get_text("words"):\n                    token = str(word[4] or "").translate(translate).strip().upper()\n                    if token in {"A", "B", "C", "D"}:\n                        token_answers.append(token)\n            if len(token_answers) == 80:\n                answers = token_answers\n        finally:\n            document.close()\n\n    if len(answers) != 80:\n        return {}\n    return {number: answers[number - 1] for number in range(1, 81)}\n'''
if old not in text:
    raise RuntimeError('answer parser fallback anchor not found')
text = text.replace(old, new, 1)

old2 = '''        if official_answer not in answer_map:\n            excluded.append({"question_number": number, "reason": "官方答案讀取失敗"})\n            continue\n\n        source_only_mode = (\n'''
new2 = '''        # Completeness rule: a database row must always remain in the paper.\n        # If an old answer sheet still cannot be parsed, keep the question and\n        # mark it ungraded instead of silently shrinking an 80-question paper.\n        answer_pending = official_answer not in answer_map\n\n        source_only_mode = (\n'''
if old2 not in text:
    raise RuntimeError('answer exclusion anchor not found')
text = text.replace(old2, new2, 1)

old3 = '''            "correct_index": answer_map[official_answer],\n            "subject": subject,\n'''
new3 = '''            "correct_index": answer_map.get(official_answer),\n            "answer_pending": answer_pending,\n            "subject": subject,\n'''
if old3 not in text:
    raise RuntimeError('correct_index anchor not found')
text = text.replace(old3, new3, 1)

path.write_text(text, encoding='utf-8')
print('guaranteed all national-exam database rows remain in the quiz')
