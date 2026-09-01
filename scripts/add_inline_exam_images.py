from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

# Insert question-image renderer before the existing whole-page fallback renderer.
anchor = '''@st.cache_data(ttl=3600, show_spinner=False)\ndef _render_pdf_page_png(url, page_number):\n'''
helper = r'''@st.cache_data(ttl=3600, show_spinner=False)
def _render_pdf_question_images(url, question_number):
    """Render only image blocks that belong to Qn, bounded by Qn and Q(n+1)."""
    pdf_bytes = _download_pdf_for_viewer(url)
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        anchors, _ = _pdf_question_anchors(url)
        qn = int(question_number)
        start_anchor = anchors.get(qn)
        next_anchor = anchors.get(qn + 1)
        if not start_anchor:
            return []

        start_page = int(start_anchor["page_index"])
        end_page = int(next_anchor["page_index"]) if next_anchor else start_page
        rendered = []

        for page_index in range(start_page, end_page + 1):
            page = document.load_page(page_index)
            page_rect = page.rect
            top = 0.0
            bottom = page_rect.height
            if page_index == start_page:
                top = max(0.0, float(start_anchor["y"]) - 4.0)
            if next_anchor and page_index == int(next_anchor["page_index"]):
                bottom = min(page_rect.height, float(next_anchor["y"]) - 4.0)

            payload = page.get_text("dict")
            for block in payload.get("blocks", []):
                if block.get("type") != 1 or not block.get("bbox"):
                    continue
                bbox = fitz.Rect(block["bbox"])
                # Image must overlap the current question's vertical range.
                if bbox.y1 <= top or bbox.y0 >= bottom:
                    continue
                # Ignore tiny decorative / accidental image objects.
                if bbox.width < 36 or bbox.height < 36:
                    continue

                pad = 4.0
                clip = fitz.Rect(
                    max(0.0, bbox.x0 - pad),
                    max(top, bbox.y0 - pad),
                    min(page_rect.width, bbox.x1 + pad),
                    min(bottom, bbox.y1 + pad),
                )
                if clip.width <= 8 or clip.height <= 8:
                    continue
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), clip=clip, alpha=False)
                rendered.append({
                    "png": pixmap.tobytes("png"),
                    "page": page_index + 1,
                })

        return rendered
    finally:
        document.close()


'''
if 'def _render_pdf_question_images(' not in text:
    if anchor not in text:
        raise RuntimeError('pdf page renderer anchor not found')
    text = text.replace(anchor, helper + anchor, 1)

# Add CSS for inline figures.
css_anchor = '''    .official-inline-link:hover { opacity:.88; }\n'''
css_insert = css_anchor + '''    .exam-inline-figure-label { color:#6b8275; font-size:.78rem; font-weight:800; text-align:center; margin:.15rem 0 .35rem; }\n'''
if '.exam-inline-figure-label' not in text:
    if css_anchor not in text:
        raise RuntimeError('inline link css anchor not found')
    text = text.replace(css_anchor, css_insert, 1)

# Replace image-question warning with true inline image rendering.
old = '''    if question.get("has_image_hint"):\n        st.info("本題含圖片，請查看官方原題後再作答。")\n    if question.get("source_url") or question.get("question_pdf_url"):\n        page_hint = question.get("source_page")\n        source_label = f"📄 查看官方原題 · PDF 第 {page_hint} 頁" if page_hint else "📄 查看官方原題"\n        st.button(\n            source_label,\n            key=f"exam_source_{index}",\n            use_container_width=True,\n            on_click=open_pdf_viewer,\n            args=(question, "national_exam_quiz"),\n        )\n'''
new = '''    if question.get("has_image_hint"):\n        inline_url = question.get("question_pdf_url") or question.get("source_url")\n        inline_number = question.get("official_question_number")\n        inline_images = []\n        if inline_url and inline_number:\n            try:\n                with st.spinner("正在載入題目圖片…"):\n                    inline_images = _render_pdf_question_images(inline_url, inline_number)\n            except Exception:\n                inline_images = []\n        if inline_images:\n            for row_start in range(0, len(inline_images), 2):\n                image_row = inline_images[row_start:row_start + 2]\n                cols = st.columns(len(image_row), gap="small")\n                for offset, (col, image_item) in enumerate(zip(cols, image_row)):\n                    with col:\n                        figure_number = row_start + offset + 1\n                        st.image(image_item["png"], use_container_width=True)\n                        st.markdown(\n                            f'<div class="exam-inline-figure-label">圖 {figure_number}</div>',\n                            unsafe_allow_html=True,\n                        )\n        else:\n            st.info("本題含圖片；圖片暫時無法自動載入，可查看官方原題。")\n    if question.get("source_url") or question.get("question_pdf_url"):\n        page_hint = question.get("source_page")\n        source_label = f"📄 查看官方原題 · PDF 第 {page_hint} 頁" if page_hint else "📄 查看官方原題"\n        st.button(\n            source_label,\n            key=f"exam_source_{index}",\n            use_container_width=True,\n            on_click=open_pdf_viewer,\n            args=(question, "national_exam_quiz"),\n        )\n'''
if old not in text:
    raise RuntimeError('image question quiz block not found')
text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
print('added inline national exam images')
