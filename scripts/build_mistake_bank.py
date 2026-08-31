from pathlib import Path

path = Path("streamlit_app.py")
text = path.read_text(encoding="utf-8")


def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, got {count}")
    text = text.replace(old, new, 1)


# datetime support for review timestamps / attempt sorting
if "from datetime import datetime, timezone\n" not in text:
    replace_once(
        "from io import BytesIO\n",
        "from io import BytesIO\nfrom datetime import datetime, timezone\n",
        "datetime import",
    )

# Session state for persistent mistake-bank flow.
state_anchor = '    "national_exam_picker_version": 0,\n'
state_new = state_anchor + (
    '    "material_mistakes_saved": False,\n'
    '    "national_exam_mistakes_saved": False,\n'
    '    "mistake_filter": "全部",\n'
    '    "mistake_subject": None,\n'
)
if '    "material_mistakes_saved": False,\n' not in text:
    replace_once(state_anchor, state_new, "mistake state")

# Reset the per-attempt save guards whenever a new attempt starts.
material_reset_anchor = "    st.session_state.quiz_finish_pending = False\n"
material_reset_new = material_reset_anchor + "    st.session_state.material_mistakes_saved = False\n"
if "    st.session_state.material_mistakes_saved = False\n" not in text[text.find("def clear_quiz_answers"):text.find("def prepare_material_upload")]:
    replace_once(material_reset_anchor, material_reset_new, "material mistake reset")

national_reset_anchor = "    st.session_state.national_exam_uncertain = {}\n"
national_reset_new = national_reset_anchor + "    st.session_state.national_exam_mistakes_saved = False\n"
if national_reset_new not in text:
    replace_once(national_reset_anchor, national_reset_new, "national mistake reset")

# Add the database adapter for the new mistake-bank experience. The old `label`
# column is intentionally reused for review status in this MVP, because error
# reason labels are no longer part of the product flow.
helper_anchor = '''def roc_year_label(year):\n    return f"{int(year) - 1911} 年"\n\n\n@st.cache_data(ttl=1800, show_spinner=False)\n'''
helper_code = r'''def roc_year_label(year):
    return f"{int(year) - 1911} 年"


_REVIEWED_PREFIX = "reviewed|"


def _mistake_is_reviewed(row):
    return str(row.get("label") or "").startswith(_REVIEWED_PREFIX)


def _parse_mistake_time(value):
    raw = str(value or "").strip()
    if not raw:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


def _mistake_attempt_identity(row):
    created = _parse_mistake_time(row.get("created_at"))
    minute_bucket = created.replace(second=0, microsecond=0)
    source_type = row.get("source_type") or "ai_document"
    if source_type == "national_exam":
        identity = (
            str(row.get("exam_year") or ""),
            str(row.get("exam_round") or ""),
            str(row.get("subject") or ""),
        )
    else:
        source = str(row.get("source") or "")
        source_base = source.split(" · Page", 1)[0].split(" · Q", 1)[0]
        identity = (source_base, str(row.get("subject") or ""))
    return minute_bucket, source_type, identity


def _mistake_question_order(row):
    number = row.get("official_question_number")
    try:
        if number is not None:
            return int(number)
    except Exception:
        pass
    try:
        return int(row.get("id") or 10**9)
    except Exception:
        return 10**9


def _sort_mistake_rows(rows):
    groups = {}
    for row in rows:
        groups.setdefault(_mistake_attempt_identity(row), []).append(row)

    grouped_rows = list(groups.values())
    grouped_rows.sort(
        key=lambda items: max(_parse_mistake_time(item.get("created_at")) for item in items),
        reverse=True,
    )

    ordered = []
    for items in grouped_rows:
        ordered.extend(sorted(items, key=_mistake_question_order))
    return ordered


def load_mistake_bank():
    response = (
        get_supabase()
        .table("mistakes")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def mark_mistake_reviewed(record_id):
    reviewed_at = datetime.now(timezone.utc).isoformat()
    (
        get_supabase()
        .table("mistakes")
        .update({"label": f"{_REVIEWED_PREFIX}{reviewed_at}"})
        .eq("id", record_id)
        .execute()
    )


def _save_mistake_rows(questions, answers, uncertain_map, source_type, meta=None, filename=None):
    meta = meta or {}
    rows = []

    for index, question in enumerate(questions):
        options = list(question.get("options") or [])
        correct_index = question.get("correct_index")
        answer_index = answers.get(index)
        uncertain = bool(uncertain_map.get(index, False))

        if answer_index is None and not uncertain:
            continue
        if correct_index not in (0, 1, 2, 3) or len(options) != 4:
            continue

        is_correct = answer_index == correct_index
        if is_correct and not uncertain:
            continue

        user_answer = options[answer_index] if answer_index in (0, 1, 2, 3) else None
        correct_answer = options[correct_index]
        subject = question.get("subject") or meta.get("subject") or st.session_state.material_subject or "未分類"

        if source_type == "national_exam":
            official_number = question.get("official_question_number", index + 1)
            source = (
                f"考選部 · {roc_year_label(meta.get('exam_year', 2026))} · "
                f"{meta.get('exam_round', '')} · {subject} · 官方第 {official_number} 題"
            )
            exam_year = meta.get("exam_year")
            exam_round = meta.get("exam_round")
            source_url = question.get("source_url")
        else:
            official_number = index + 1
            page_number = question.get("source_page")
            source = f"教材 · {filename or '上傳教材'}"
            if page_number:
                source += f" · Page {page_number}"
            source += f" · Q{index + 1}"
            exam_year = None
            exam_round = None
            source_url = None

        rows.append({
            "subject": subject,
            "concept": question.get("concept") or "未分類",
            "question": question.get("question") or "",
            "options": options,
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "uncertain": uncertain,
            "is_correct": is_correct,
            "label": "pending",
            "source": source,
            "explanation": question.get("explanation") or "",
            "review_points": question.get("review_points") or [],
            "source_quote": question.get("source_quote") or "",
            "source_type": source_type,
            "exam_year": exam_year,
            "exam_round": exam_round,
            "official_question_number": official_number,
            "source_url": source_url,
        })

    if rows:
        get_supabase().table("mistakes").insert(rows).execute()


def save_material_mistakes_if_needed():
    if st.session_state.material_mistakes_saved:
        return
    _save_mistake_rows(
        st.session_state.material_questions or [],
        st.session_state.quiz_answers,
        st.session_state.quiz_uncertain,
        "ai_document",
        filename=st.session_state.uploaded_learning_file,
    )
    st.session_state.material_mistakes_saved = True


def save_national_exam_mistakes_if_needed():
    if st.session_state.national_exam_mistakes_saved:
        return
    _save_mistake_rows(
        st.session_state.national_exam_questions or [],
        st.session_state.national_exam_answers,
        st.session_state.national_exam_uncertain,
        "national_exam",
        meta=st.session_state.national_exam_meta or {},
    )
    st.session_state.national_exam_mistakes_saved = True


@st.cache_data(ttl=1800, show_spinner=False)
'''
if "def load_mistake_bank():" not in text:
    replace_once(helper_anchor, helper_code, "mistake database helpers")

# Mistake-bank visuals.
css_anchor = '    .slime { width:178px; height:142px; margin:0 auto 1rem;'
css_block = r'''    .mistake-summary { background:linear-gradient(135deg,#edf9f1,#f7fcf9); border:1px solid #dcebe2; border-radius:20px; padding:1rem 1.15rem; margin:.7rem 0 1rem; color:#315b47; }
    .mistake-summary strong { color:#22985a; font-size:1.08rem; }
    [class*="st-key-mistake_folder_"] { background:rgba(255,255,255,.96); border:1px solid #dceae2; border-radius:22px; padding:1.05rem 1.05rem .9rem; box-shadow:0 10px 26px rgba(31,83,53,.045); min-height:145px; }
    .mistake-folder-icon { font-size:1.75rem; margin-bottom:.5rem; }
    .mistake-folder-title { color:#173b2b; font-size:1.08rem; font-weight:950; line-height:1.4; }
    .mistake-folder-meta { color:#70877a; font-size:.88rem; margin:.35rem 0 .7rem; }
    .mistake-folder-pending { color:#2aa665; font-weight:900; }
    .mistake-row-question { color:#173b2b; font-size:1.05rem; font-weight:850; line-height:1.6; margin:.4rem 0 .8rem; }
    .mistake-status { display:inline-flex; align-items:center; border-radius:999px; padding:.2rem .55rem; font-size:.75rem; font-weight:900; margin-right:.35rem; }
    .mistake-status.wrong { background:#fdecec; color:#c84e4e; }
    .mistake-status.uncertain { background:#fff4d7; color:#ad7c14; }
    .mistake-status.reviewed { background:#e9f7ee; color:#2c8d58; }
    [class*="st-key-mistake_reviewed_"] { opacity:.7; }
    .mistake-source { color:#70877a; font-size:.84rem; line-height:1.55; margin-top:.75rem; }

'''
if ".mistake-summary {" not in text:
    replace_once(css_anchor, css_block + css_anchor, "mistake css")

# Open the mistake bank from Study.
old_study = '[("📘", "我要複習錯題", "回顧答錯或不確定的題目，加強你的弱點。", None), ("⏱️", "我要專心讀書", "進入專注計時器，累積今天的學習效率。", None)],'
new_study = '[("📘", "我要複習錯題", "回顧答錯或不確定的題目，加強你的弱點。", "mistakes"), ("⏱️", "我要專心讀書", "進入專注計時器，累積今天的學習效率。", None)],'
if new_study not in text:
    replace_once(old_study, new_study, "mistake study entry")

# Drawer treats the mistake pages as part of Study.
old_active = '    if active.startswith("study_material") or active.startswith("quiz") or active.startswith("national_exam"):\n'
new_active = '    if active.startswith("study_material") or active.startswith("quiz") or active.startswith("national_exam") or active.startswith("mistake"):\n'
if new_active not in text:
    replace_once(old_active, new_active, "drawer mistake active")

# Persist mistakes when a result page is reached. Failure should not block results.
material_result_anchor = '''    st.markdown(f'<div class="study-header"><div class="eyebrow">RESULT</div><div class="hero-title" style="font-size:2.05rem">完成 {QUIZ_SIZE} 題測驗</div><div class="hero-copy">真正掌握 {correct} / {QUIZ_SIZE} 題。答對但標記 ❓ 的題目仍會列入複習。</div></div>', unsafe_allow_html=True)\n'''
material_result_new = '''    try:\n        save_material_mistakes_if_needed()\n    except Exception:\n        st.warning("這次錯題暫時無法同步到錯題庫，但測驗結果仍可正常查看。")\n\n''' + material_result_anchor
if "save_material_mistakes_if_needed()" not in text[text.find("def material_quiz_result"):text.find("# =========================================================\n# Other MVP pages")]:
    replace_once(material_result_anchor, material_result_new, "save material mistakes")

national_result_anchor = '''    subtitle = f'{roc_year_label(meta.get("exam_year", 2026))} · {meta.get("exam_round", "")} · {html.escape(str(meta.get("subject", "")))}'\n'''
national_result_new = '''    try:\n        save_national_exam_mistakes_if_needed()\n    except Exception:\n        st.warning("這次錯題暫時無法同步到錯題庫，但測驗結果仍可正常查看。")\n\n''' + national_result_anchor
national_section_start = text.find("def national_exam_result_page")
national_section_end = text.find("def study_material_intro")
if "save_national_exam_mistakes_if_needed()" not in text[national_section_start:national_section_end]:
    replace_once(national_result_anchor, national_result_new, "save national mistakes")

# Folder-style mistake bank and subject detail page.
ui_anchor = '''# =========================================================\n# Other MVP pages\n# =========================================================\n\n'''
ui_code = r'''# =========================================================
# Mistake bank
# =========================================================


def _mistake_filter_rows(rows, source_filter):
    if source_filter == "教材":
        return [row for row in rows if (row.get("source_type") or "ai_document") != "national_exam"]
    if source_filter == "國考":
        return [row for row in rows if row.get("source_type") == "national_exam"]
    return list(rows)


def _mistake_options(row):
    options = row.get("options") or []
    if isinstance(options, str):
        try:
            options = json.loads(options)
        except Exception:
            options = []
    return list(options)


def _mistake_review_points(row):
    points = row.get("review_points") or []
    if isinstance(points, str):
        try:
            points = json.loads(points)
        except Exception:
            points = [points] if points else []
    return list(points)


def _mistake_options_markup(row):
    options = _mistake_options(row)
    user_answer = row.get("user_answer")
    correct_answer = row.get("correct_answer")
    letters = ["A", "B", "C", "D"]
    rendered = []
    for index, option in enumerate(options):
        cls = "review-option"
        if option == correct_answer:
            cls += " correct"
        elif user_answer is not None and option == user_answer:
            cls += " wrong"
        letter = letters[index] if index < len(letters) else str(index + 1)
        rendered.append(
            f'<div class="{cls}"><span class="review-option-letter">{letter}</span>'
            f'{html.escape(normalize_scientific_notation(option))}</div>'
        )
    return '<div class="review-options">' + ''.join(rendered) + '</div>'


def _mistake_source_tag(row):
    return "國考" if row.get("source_type") == "national_exam" else "教材"


def _render_mistake_record(row, reviewed):
    record_id = row.get("id")
    question = normalize_scientific_notation(row.get("question") or "")
    question_number = row.get("official_question_number")
    source_tag = _mistake_source_tag(row)
    state_text = "不確定" if row.get("uncertain") else "答錯"
    number_text = f"第 {question_number} 題 · " if question_number is not None else ""
    preview = question if len(question) <= 58 else question[:58] + "…"
    expander_title = f"{source_tag} · {state_text} · {number_text}{preview}"

    container_key = f"mistake_reviewed_{record_id}" if reviewed else f"mistake_pending_{record_id}"
    with st.container(key=container_key):
        with st.expander(expander_title):
            status_class = "uncertain" if row.get("uncertain") else "wrong"
            reviewed_badge = '<span class="mistake-status reviewed">✓ 已複習</span>' if reviewed else ""
            st.markdown(
                f'<span class="mistake-status {status_class}">{state_text}</span>{reviewed_badge}'
                f'<div class="mistake-row-question">{html.escape(question)}</div>'
                f'{_mistake_options_markup(row)}',
                unsafe_allow_html=True,
            )

            explanation = str(row.get("explanation") or "").strip()
            if explanation:
                st.markdown("**解析**")
                st.write(explanation)

            points = _mistake_review_points(row)
            if points:
                st.markdown("**複習重點**")
                for point in points:
                    st.markdown(f"- {point}")

            source_quote = str(row.get("source_quote") or "").strip()
            if source_quote:
                st.markdown("**教材依據**")
                st.markdown(f"> {source_quote}")

            source = str(row.get("source") or "").strip()
            if source:
                st.markdown(f'<div class="mistake-source">來源：{html.escape(source)}</div>', unsafe_allow_html=True)

            if row.get("source_url"):
                st.link_button("查看官方原題 ↗", row["source_url"])

            if not reviewed:
                if st.button("✓ 已複習", type="primary", key=f"mark_reviewed_{record_id}"):
                    try:
                        mark_mistake_reviewed(record_id)
                        st.rerun()
                    except Exception as error:
                        st.error("目前無法更新複習狀態。")
                        st.caption(f"{type(error).__name__}: {error}")


def mistake_bank_page():
    topbar()
    render_back_button("返回學習", "study", "back_mistakes")
    st.markdown('<div class="study-header"><div class="eyebrow">MISTAKE BANK</div><div class="hero-title" style="font-size:2.05rem">我要複習錯題</div><div class="hero-copy">先選來源，再打開科目資料夾，一題一題把解析看懂。</div></div>', unsafe_allow_html=True)

    filters = ["全部", "教材", "國考"]
    current_filter = st.session_state.mistake_filter if st.session_state.mistake_filter in filters else "全部"
    source_filter = st.radio(
        "錯題來源",
        filters,
        horizontal=True,
        index=filters.index(current_filter),
        key="mistake_source_filter",
        label_visibility="collapsed",
    )
    st.session_state.mistake_filter = source_filter

    try:
        rows = load_mistake_bank()
    except Exception as error:
        st.error("目前無法讀取錯題庫。")
        st.caption(f"{type(error).__name__}: {error}")
        return

    rows = _mistake_filter_rows(rows, source_filter)
    pending_count = sum(1 for row in rows if not _mistake_is_reviewed(row))
    reviewed_count = len(rows) - pending_count
    st.markdown(
        f'<div class="mistake-summary">尚未複習 <strong>{pending_count}</strong> 題 · 已複習 {reviewed_count} 題 · 共 {len(rows)} 題</div>',
        unsafe_allow_html=True,
    )

    if not rows:
        st.info("目前這個分類還沒有錯題。完成教材或國考測驗後，答錯或標記 ❓ 的題目會自動出現在這裡。")
        return

    by_subject = {}
    for row in rows:
        subject = str(row.get("subject") or "未分類")
        by_subject.setdefault(subject, []).append(row)

    subjects = sorted(
        by_subject,
        key=lambda subject: max(_parse_mistake_time(item.get("created_at")) for item in by_subject[subject]),
        reverse=True,
    )

    cols = st.columns(3, gap="medium")
    for index, subject in enumerate(subjects):
        subject_rows = by_subject[subject]
        pending = sum(1 for row in subject_rows if not _mistake_is_reviewed(row))
        with cols[index % 3]:
            with st.container(key=f"mistake_folder_{index}"):
                st.markdown(
                    f'<div class="mistake-folder-icon">📁</div>'
                    f'<div class="mistake-folder-title">{html.escape(subject)}</div>'
                    f'<div class="mistake-folder-meta"><span class="mistake-folder-pending">{pending} 題尚未複習</span> · 共 {len(subject_rows)} 題</div>',
                    unsafe_allow_html=True,
                )
                if st.button("開啟資料夾 →", use_container_width=True, key=f"open_mistake_folder_{index}"):
                    st.session_state.mistake_subject = subject
                    goto("mistake_subject")


def mistake_subject_page():
    subject = st.session_state.mistake_subject
    if not subject:
        goto("mistakes")

    topbar()
    render_back_button("返回錯題庫", "mistakes", "back_mistake_subject")
    source_filter = st.session_state.mistake_filter or "全部"
    st.markdown(
        f'<div class="study-header"><div class="eyebrow">{html.escape(source_filter)}</div>'
        f'<div class="hero-title" style="font-size:2.05rem">📁 {html.escape(str(subject))}</div>'
        f'<div class="hero-copy">尚未複習的題目會排在前面；同一區依完成測驗的時間由新到舊排列。</div></div>',
        unsafe_allow_html=True,
    )

    try:
        rows = load_mistake_bank()
    except Exception as error:
        st.error("目前無法讀取錯題庫。")
        st.caption(f"{type(error).__name__}: {error}")
        return

    rows = [
        row for row in _mistake_filter_rows(rows, source_filter)
        if str(row.get("subject") or "未分類") == str(subject)
    ]
    pending_rows = _sort_mistake_rows([row for row in rows if not _mistake_is_reviewed(row)])
    reviewed_rows = _sort_mistake_rows([row for row in rows if _mistake_is_reviewed(row)])

    st.markdown(f'<div class="section-title">尚未複習 · {len(pending_rows)} 題</div>', unsafe_allow_html=True)
    if not pending_rows:
        st.success("這個資料夾目前沒有尚未複習的題目。")
    for row in pending_rows:
        _render_mistake_record(row, reviewed=False)

    if reviewed_rows:
        st.markdown(f'<div class="section-title">已複習 · {len(reviewed_rows)} 題</div>', unsafe_allow_html=True)
        for row in reviewed_rows:
            _render_mistake_record(row, reviewed=True)


''' + ui_anchor
if "def mistake_bank_page():" not in text:
    replace_once(ui_anchor, ui_code, "mistake bank ui")

# Routes.
dispatch_anchor = '''elif page == "quiz_result":\n    material_quiz_result()\nelif page == "slime":\n'''
dispatch_new = '''elif page == "quiz_result":\n    material_quiz_result()\nelif page == "mistakes":\n    mistake_bank_page()\nelif page == "mistake_subject":\n    mistake_subject_page()\nelif page == "slime":\n'''
if 'elif page == "mistakes":\n' not in text:
    replace_once(dispatch_anchor, dispatch_new, "mistake routes")

path.write_text(text, encoding="utf-8")
print("MedSlime mistake bank patch applied")
