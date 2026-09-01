from pathlib import Path

app = Path('streamlit_app.py')
text = app.read_text(encoding='utf-8')

# Imports
old = 'import time\nfrom urllib.parse import urlsplit, urlunsplit, parse_qs\nfrom io import BytesIO\n'
new = 'import time\nimport urllib.request\nfrom urllib.parse import urlsplit, urlunsplit, parse_qs\nfrom io import BytesIO\n'
if old not in text:
    raise RuntimeError('import anchor not found')
text = text.replace(old, new, 1)

old = 'import streamlit as st\nfrom openai import OpenAI\n'
new = 'import streamlit as st\nimport fitz\nfrom openai import OpenAI\n'
if old not in text:
    raise RuntimeError('third party import anchor not found')
text = text.replace(old, new, 1)

# Session state
anchor = '    "national_exam_picker_version": 0,\n'
insert = anchor + '    "pdf_viewer_url": None,\n    "pdf_viewer_page": None,\n    "pdf_viewer_title": None,\n    "pdf_viewer_return_page": "national_exam_quiz",\n'
if '"pdf_viewer_url"' not in text:
    if anchor not in text:
        raise RuntimeError('state anchor not found')
    text = text.replace(anchor, insert, 1)

# Helpers, placed before navigation/shared visuals.
anchor = '\n# =========================================================\n# Navigation / shared visuals\n# =========================================================\n'
helpers = r'''
@st.cache_data(ttl=3600, show_spinner=False)
def _download_pdf_for_viewer(url):
    raw = str(url or "").strip()
    if not raw.startswith(("https://", "http://")):
        raise ValueError("PDF 網址格式不正確。")
    # Fragments are browser-only and must not be sent to the server.
    parts = urlsplit(raw)
    raw = urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))
    request = urllib.request.Request(
        raw,
        headers={
            "User-Agent": "Mozilla/5.0 (MedSlime PDF viewer)",
            "Accept": "application/pdf,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()
    if not data:
        raise ValueError("官方 PDF 沒有回傳內容。")
    return data


@st.cache_data(ttl=3600, show_spinner=False)
def _render_pdf_page_png(url, page_number):
    pdf_bytes = _download_pdf_for_viewer(url)
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        if document.page_count <= 0:
            raise ValueError("PDF 沒有可顯示的頁面。")
        page_number = max(1, min(int(page_number or 1), document.page_count))
        page = document.load_page(page_number - 1)
        # 1.7x keeps text readable on phones without producing an enormous image.
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.7, 1.7), alpha=False)
        return pixmap.tobytes("png"), page_number, document.page_count
    finally:
        document.close()


def open_pdf_viewer(question, return_page="national_exam_quiz"):
    pdf_url = question.get("question_pdf_url") or question.get("source_url") or question.get("source_page_url")
    page_hint = question.get("source_page") or _extract_pdf_page_hint(question.get("source_page_url")) or _extract_pdf_page_hint(question.get("source_url"))
    if not pdf_url:
        st.session_state.national_exam_load_error = "這題目前沒有官方 PDF 連結。"
        return
    st.session_state.pdf_viewer_url = str(pdf_url)
    st.session_state.pdf_viewer_page = int(page_hint or 1)
    official = question.get("official_question_number")
    st.session_state.pdf_viewer_title = f"官方原題 · 第 {official} 題" if official else "官方原題"
    st.session_state.pdf_viewer_return_page = return_page
    st.session_state.medslime_page = "pdf_viewer"
    st.session_state.menu_open = False


def pdf_viewer_page():
    topbar()
    return_page = st.session_state.pdf_viewer_return_page or "national_exam_quiz"
    render_back_button("返回題目", return_page, "back_pdf_viewer")
    url = st.session_state.pdf_viewer_url
    page_number = st.session_state.pdf_viewer_page or 1
    title = st.session_state.pdf_viewer_title or "官方原題"
    st.markdown(
        f'<div class="study-header"><div class="eyebrow">SOURCE</div>'
        f'<div class="hero-title" style="font-size:2rem">{html.escape(str(title))}</div>'
        f'<div class="hero-copy">直接顯示原 PDF 的定位頁，不依賴手機瀏覽器的 PDF 跳頁功能。</div></div>',
        unsafe_allow_html=True,
    )
    if not url:
        st.error("找不到這題的官方 PDF。")
        return
    try:
        with st.spinner("正在載入官方原題…"):
            png_bytes, shown_page, page_count = _render_pdf_page_png(url, page_number)
        st.caption(f"PDF 第 {shown_page} / {page_count} 頁")
        st.image(png_bytes, use_container_width=True)
        clean_url = urlunsplit((*urlsplit(str(url))[:4], ""))
        st.link_button("開啟完整官方 PDF ↗", clean_url, use_container_width=True)
    except Exception as error:
        st.error("原題頁面暫時無法載入，但仍可以開啟完整官方 PDF。")
        st.caption(f"{type(error).__name__}: {error}")
        st.link_button("開啟完整官方 PDF ↗", str(url), use_container_width=True)

'''
if 'def pdf_viewer_page()' not in text:
    if anchor not in text:
        raise RuntimeError('nav anchor not found')
    text = text.replace(anchor, '\n' + helpers + anchor, 1)

# Quiz source link: stop sending users directly into Safari PDF viewer.
old = '''    source_link = ""\n    if question.get("source_url"):\n        safe_url = html.escape(str(question["source_url"]), quote=True)\n        page_hint = question.get("source_page")\n        link_label = f"官方原題 · Page {page_hint} ↗" if page_hint else "官方原題 ↗"\n        source_link = f'<a class="official-inline-link" href="{safe_url}" target="_blank" rel="noopener noreferrer">{link_label}</a>'\n    safe_exam_question = html.escape(normalize_scientific_notation(question["question"]))\n    st.markdown(\n        f'<div class="quiz-card"><div class="quiz-meta-row"><div class="eyebrow">{progress_text}</div>{source_link}</div><div class="quiz-question">{safe_exam_question}</div></div>',\n        unsafe_allow_html=True,\n    )\n'''
new = '''    safe_exam_question = html.escape(normalize_scientific_notation(question["question"]))\n    st.markdown(\n        f'<div class="quiz-card"><div class="quiz-meta-row"><div class="eyebrow">{progress_text}</div></div><div class="quiz-question">{safe_exam_question}</div></div>',\n        unsafe_allow_html=True,\n    )\n    if question.get("source_url") or question.get("question_pdf_url"):\n        page_hint = question.get("source_page")\n        source_label = f"📄 查看官方原題 · PDF 第 {page_hint} 頁" if page_hint else "📄 查看官方原題"\n        st.button(\n            source_label,\n            key=f"exam_source_{index}",\n            use_container_width=True,\n            on_click=open_pdf_viewer,\n            args=(question, "national_exam_quiz"),\n        )\n'''
if old not in text:
    raise RuntimeError('quiz source block anchor not found')
text = text.replace(old, new, 1)

# Result page source button also goes to internal viewer.
old = '''            if question.get("source_url"):\n                page_hint = question.get("source_page")\n                label = f"查看官方原題 · Page {page_hint} ↗" if page_hint else "查看官方原題 ↗"\n                st.link_button(label, question["source_url"])\n'''
new = '''            if question.get("source_url") or question.get("question_pdf_url"):\n                page_hint = question.get("source_page")\n                label = f"📄 查看官方原題 · PDF 第 {page_hint} 頁" if page_hint else "📄 查看官方原題"\n                st.button(\n                    label,\n                    key=f"exam_result_source_{index}",\n                    use_container_width=True,\n                    on_click=open_pdf_viewer,\n                    args=(question, "national_exam_result"),\n                )\n'''
if old not in text:
    raise RuntimeError('result source block anchor not found')
text = text.replace(old, new, 1)

# Router
anchor = 'elif page == "national_exam_result":\n    national_exam_result_page()\n'
replacement = anchor + 'elif page == "pdf_viewer":\n    pdf_viewer_page()\n'
if 'elif page == "pdf_viewer":' not in text:
    if anchor not in text:
        raise RuntimeError('router anchor not found')
    text = text.replace(anchor, replacement, 1)

app.write_text(text, encoding='utf-8')

req = Path('requirements.txt')
req_text = req.read_text(encoding='utf-8')
if 'PyMuPDF' not in req_text and 'pymupdf' not in req_text.lower():
    req_text = req_text.rstrip() + '\nPyMuPDF>=1.24.0\n'
    req.write_text(req_text, encoding='utf-8')

print('added internal page-rendering PDF viewer')
