from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

start = text.find('@st.cache_data(ttl=3600, show_spinner=False)\ndef _render_pdf_question_images')
end = text.find('\n\n@st.cache_data(ttl=3600, show_spinner=False)\ndef _render_pdf_page_png', start)
if start == -1 or end == -1:
    raise RuntimeError('inline image helper not found')

new_helper = r'''@st.cache_data(ttl=3600, show_spinner=False)
def _render_pdf_question_images(url, question_number):
    """Render figures belonging to Qn.

    Prefer true PDF image blocks. If the PDF does not expose figures as image
    objects, fall back to rendering the visual gap between the question stem
    and option A (or the page bottom for a cross-page stem such as Q68).
    """
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

        # First pass: true image blocks.
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
                if bbox.y1 <= top or bbox.y0 >= bottom:
                    continue
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
                rendered.append({"png": pixmap.tobytes("png"), "page": page_index + 1})

        if rendered:
            return rendered

        # Fallback: many MoEx PDFs visually contain figures but do not expose
        # them as standalone image blocks. Find the large visual band after the
        # stem text and before option A / the next question, then render it.
        fallback = []
        option_re = re.compile(r"^[AＡ][\.．、\)）]\s*")

        for page_index in range(start_page, end_page + 1):
            page = document.load_page(page_index)
            page_rect = page.rect
            q_top = 0.0
            q_bottom = page_rect.height
            if page_index == start_page:
                q_top = max(0.0, float(start_anchor["y"]) - 2.0)
            if next_anchor and page_index == int(next_anchor["page_index"]):
                q_bottom = min(page_rect.height, float(next_anchor["y"]) - 4.0)

            payload = page.get_text("dict")
            lines = []
            for block in payload.get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    bbox = line.get("bbox")
                    spans = line.get("spans", [])
                    if not bbox or not spans:
                        continue
                    line_text = "".join(str(span.get("text", "")) for span in spans).strip()
                    if not line_text:
                        continue
                    y0, y1 = float(bbox[1]), float(bbox[3])
                    if y1 <= q_top or y0 >= q_bottom:
                        continue
                    lines.append({"text": line_text, "y0": y0, "y1": y1})

            lines.sort(key=lambda item: item["y0"])
            if not lines:
                continue

            option_a = next((line for line in lines if option_re.match(line["text"])), None)
            if option_a:
                before_a = [line for line in lines if line["y1"] < option_a["y0"] - 2.0]
                if not before_a:
                    continue
                visual_top = max(line["y1"] for line in before_a) + 6.0
                visual_bottom = option_a["y0"] - 6.0
            else:
                # Cross-page question: on the stem page, the figures often sit
                # below the final extracted text line and run to the page bottom.
                visual_top = max(line["y1"] for line in lines) + 6.0
                visual_bottom = q_bottom - 8.0

            # Require a substantial band so normal text-only questions do not
            # accidentally render blank whitespace as an inline image.
            if visual_bottom - visual_top < 70.0:
                continue

            clip = fitz.Rect(
                26.0,
                max(q_top, visual_top),
                max(27.0, page_rect.width - 26.0),
                min(q_bottom, visual_bottom),
            )
            if clip.width <= 40 or clip.height <= 70:
                continue
            pixmap = page.get_pixmap(matrix=fitz.Matrix(1.9, 1.9), clip=clip, alpha=False)
            fallback.append({"png": pixmap.tobytes("png"), "page": page_index + 1})

        return fallback
    finally:
        document.close()
'''

text = text[:start] + new_helper + text[end:]

# Make fallback crops use a neutral label rather than guessing figure count.
old = '''                        figure_number = row_start + offset + 1\n                        st.image(image_item["png"], use_container_width=True)\n                        st.markdown(\n                            f'<div class="exam-inline-figure-label">圖 {figure_number}</div>',\n                            unsafe_allow_html=True,\n                        )\n'''
new = '''                        st.image(image_item["png"], use_container_width=True)\n                        if len(inline_images) > 1:\n                            st.markdown(\n                                f'<div class="exam-inline-figure-label">題目圖片 {row_start + offset + 1}</div>',\n                                unsafe_allow_html=True,\n                            )\n'''
if old in text:
    text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
print('added rendered-gap fallback for inline exam images')
