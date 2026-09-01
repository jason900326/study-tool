from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

start = text.index('@st.cache_data(ttl=86400, show_spinner=False)\ndef _load_official_answer_key')
end = text.index('\n\ndef clear_national_exam_answers()', start)

replacement = r'''@st.cache_data(ttl=86400, show_spinner=False)
def _load_official_answer_key(answer_pdf_url):
    """Read one MOEX answer-sheet PDF and return the official 1..80 answer key."""
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
    # MOEX answer sheets contain four lines beginning with 答案, 20 answers per line,
    # followed by a note/table of question numbers. Parse only those answer lines.
    answers = []
    for line in normalized.splitlines():
        compact = line.strip()
        if compact.startswith("備"):
            break
        if not compact.startswith("答案"):
            continue
        letters = re.findall(r"(?<![A-Za-z])[ABCD](?![A-Za-z])", compact.upper())
        answers.extend(letters)

    if len(answers) != 80:
        # Defensive fallback: only inspect the 標準答案 -> 備註 section.
        section = normalized
        if "標準答案：" in section:
            section = section.split("標準答案：", 1)[1]
        if "備" in section:
            section = section.split("備", 1)[0]
        answers = re.findall(r"(?<![A-Za-z])[ABCD](?![A-Za-z])", section.upper())

    if len(answers) != 80:
        return {}
    return {number: answers[number - 1] for number in range(1, 81)}


def load_national_exam_paper(exam_year, exam_round, subject):
    """Load every database row; official MOEX answer sheet is the canonical answer source."""
    supabase = get_supabase()
    response = (
        supabase
        .table("national_exam_questions")
        .select(
            "id, exam_year, exam_round, subject, question_number, question, options, "
            "correct_answers, source_page_url, question_pdf_url, answer_pdf_url, corrected_answer_pdf_url, "
            "has_image_hint, parse_status"
        )
        .eq("exam_year", exam_year)
        .eq("exam_round", exam_round)
        .eq("subject", subject)
        .order("question_number")
        .limit(100)
        .execute()
    )
    rows = response.data or []
    answer_map = {"A": 0, "B": 1, "C": 2, "D": 3}
    usable, excluded = [], []

    # Every paper is 80 rows. Read its official answer sheet once and use it for all 80.
    answer_url = None
    for row in rows:
        candidate = row.get("corrected_answer_pdf_url") or row.get("answer_pdf_url")
        if candidate:
            answer_url = candidate
            break

    try:
        official_answers = _load_official_answer_key(answer_url) if answer_url else {}
    except Exception:
        official_answers = {}

    for row in rows:
        number = int(row.get("question_number") or 0)
        options = list(row.get("options") or [])
        has_image_hint = bool(row.get("has_image_hint"))

        official_answer = official_answers.get(number)
        if official_answer not in answer_map:
            # Only use the stored answer as an emergency fallback when it is already a valid single answer.
            stored = list(row.get("correct_answers") or [])
            if len(stored) == 1 and stored[0] in answer_map:
                official_answer = stored[0]

        if official_answer not in answer_map:
            excluded.append({"question_number": number, "reason": "官方答案讀取失敗"})
            continue

        source_only_mode = (
            row.get("parse_status") != "ok"
            or len(options) != 4
            or any(not str(option or "").strip() for option in options)
        )
        if source_only_mode:
            options = ["A", "B", "C", "D"]

        question_text = str(row.get("question") or "").strip()
        if not question_text:
            question_text = f"官方第 {number} 題（題目內容請查看官方原題）"

        usable.append({
            "question": question_text,
            "options": options,
            "correct_index": answer_map[official_answer],
            "subject": subject,
            "concept": "歷屆國考真題",
            "explanation": "",
            "review_points": [],
            "source_url": pdf_deep_link(row.get("question_pdf_url"), row.get("source_page_url")),
            "question_pdf_url": row.get("question_pdf_url"),
            "source_page_url": row.get("source_page_url"),
            "source_page": _extract_pdf_page_hint(row.get("source_page_url")) or _extract_pdf_page_hint(row.get("question_pdf_url")),
            "has_image_hint": has_image_hint,
            "image_choice_mode": source_only_mode,
            "source_only_mode": source_only_mode,
            "official_question_number": number,
            "national_exam_id": row.get("id"),
        })

    return usable, excluded, len(rows)
'''

text = text[:start] + replacement + text[end:]
path.write_text(text, encoding='utf-8')
print('official answer sheet is now canonical for all exam rows')
