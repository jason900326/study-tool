from pathlib import Path
import re

app = Path('streamlit_app.py')
text = app.read_text(encoding='utf-8')

# Add viewer state for official question number.
anchor = '    "pdf_viewer_page": None,\n'
if '"pdf_viewer_question_number"' not in text:
    if anchor not in text:
        raise RuntimeError('pdf viewer state anchor not found')
    text = text.replace(anchor, anchor + '    "pdf_viewer_question_number": None,\n', 1)

# Replace the old whole-page renderer with question-aware crop helpers.
start = text.find('@st.cache_data(ttl=3600, show_spinner=False)\ndef _render_pdf_page_png')
end = text.find('\n\ndef open_pdf_viewer(', start)
if start == -1 or end == -1:
    raise RuntimeError('old pdf page renderer not found')

new_helpers = r'''@st.cache_data(ttl=3600, show_spinner=False)
def _pdf_question_anchors(url):
    """Locate numbered-question starts using PDF text coordinates."""
    pdf_bytes = _download_pdf_for_viewer(url)
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    anchors = {}
    try:
        for page_index in range(document.page_count):
            page = document.load_page(page_index)
            payload = page.get_text("dict")
            for block in payload.get("blocks", []):
                if block.get("type") != 0:
                    continue
                for line in block.get("lines", []):
                    spans = line.get("spans", [])
                    if not spans:
                        continue
                    line_text = "".join(str(span.get("text", "")) for span in spans).strip()
                    # Official exams consistently begin questions as 1. ... / 11. ...
                    match = re.match(r"^(\d{1,3})\s*[\.．、]\s*", line_text)
                    if not match:
                        continue
                    number = int(match.group(1))
                    if not (1 <= number <= 200):
                        continue
                    bbox = line.get("bbox")
                    if bbox and number not in anchors:
                        anchors[number] = {
                            "page_index": page_index,
                            "y": float(bbox[1]),
                            "text": line_text,
                        }
        return anchors, document.page_count
    finally:
        document.close()


@st.cache_data(ttl=3600, show_spinner=False)
def _render_pdf_question_crops(url, question_number):
    """Crop the original PDF from Qn start to Q(n+1), including page breaks."""
    pdf_bytes = _download_pdf_for_viewer(url)
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        anchors, page_count = _pdf_question_anchors(url)
        qn = int(question_number)
        start_anchor = anchors.get(qn)
        next_anchor = anchors.get(qn + 1)
        if not start_anchor:
            raise ValueError(f"找不到官方第 {qn} 題的起點。")

        start_page = int(start_anchor["page_index"])
        end_page = int(next_anchor["page_index"]) if next_anchor else start_page
        margin_x = 24.0
        margin_y = 10.0
        rendered = []

        for page_index in range(start_page, end_page + 1):
            page = document.load_page(page_index)
            rect = page.rect
            top = 18.0
            bottom = rect.height - 18.0

            if page_index == start_page:
                top = max(0.0, float(start_anchor["y"]) - margin_y)
            if next_anchor and page_index == int(next_anchor["page_index"]):
                bottom = min(rect.height, float(next_anchor["y"]) - margin_y)

            if bottom <= top + 8:
                continue

            clip = fitz.Rect(
                max(0.0, margin_x),
                top,
                max(margin_x + 1, rect.width - margin_x),
                bottom,
            )
            pixmap = page.get_pixmap(matrix=fitz.Matrix(1.85, 1.85), clip=clip, alpha=False)
            rendered.append({
                "png": pixmap.tobytes("png"),
                "page": page_index + 1,
            })

        if not rendered:
            raise ValueError("定位成功，但沒有可顯示的題目區域。")
        return rendered, page_count
    finally:
        document.close()


@st.cache_data(ttl=3600, show_spinner=False)
def _render_pdf_page_png(url, page_number):
    """Fallback whole-page renderer when question-coordinate detection fails."""
    pdf_bytes = _download_pdf_for_viewer(url)
    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        if document.page_count <= 0:
            raise ValueError("PDF 沒有可顯示的頁面。")
        page_number = max(1, min(int(page_number or 1), document.page_count))
        page = document.load_page(page_number - 1)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.7, 1.7), alpha=False)
        return pixmap.tobytes("png"), page_number, document.page_count
    finally:
        document.close()
'''
text = text[:start] + new_helpers + text[end:]

# Store question number whenever the source viewer opens.
old = '''    st.session_state.pdf_viewer_url = str(pdf_url)\n    st.session_state.pdf_viewer_page = int(page_hint or 1)\n    official = question.get("official_question_number")\n    st.session_state.pdf_viewer_title = f"官方原題 · 第 {official} 題" if official else "官方原題"\n'''
new = '''    st.session_state.pdf_viewer_url = str(pdf_url)\n    st.session_state.pdf_viewer_page = int(page_hint or 1)\n    official = question.get("official_question_number")\n    st.session_state.pdf_viewer_question_number = int(official) if official is not None else None\n    st.session_state.pdf_viewer_title = f"官方原題 · 第 {official} 題" if official else "官方原題"\n'''
if old not in text:
    raise RuntimeError('open_pdf_viewer state block not found')
text = text.replace(old, new, 1)

# Replace viewer rendering with question crops + fallback.
old = '''    try:\n        with st.spinner("正在載入官方原題…"):\n            png_bytes, shown_page, page_count = _render_pdf_page_png(url, page_number)\n        st.caption(f"PDF 第 {shown_page} / {page_count} 頁")\n        st.image(png_bytes, use_container_width=True)\n        clean_url = urlunsplit((*urlsplit(str(url))[:4], ""))\n        st.link_button("開啟完整官方 PDF ↗", clean_url, use_container_width=True)\n    except Exception as error:\n        st.error("原題頁面暫時無法載入，但仍可以開啟完整官方 PDF。")\n        st.caption(f"{type(error).__name__}: {error}")\n        st.link_button("開啟完整官方 PDF ↗", str(url), use_container_width=True)\n'''
new = '''    try:\n        question_number = st.session_state.pdf_viewer_question_number\n        if question_number:\n            try:\n                with st.spinner("正在定位官方原題…"):\n                    crops, page_count = _render_pdf_question_crops(url, question_number)\n                page_labels = "、".join(str(item["page"]) for item in crops)\n                st.caption(f"已定位官方第 {question_number} 題 · PDF 第 {page_labels} 頁")\n                for crop_index, item in enumerate(crops):\n                    if len(crops) > 1:\n                        st.markdown(\n                            f'<div class="eyebrow" style="margin:.65rem 0 .35rem">原題片段 {crop_index + 1} · PDF Page {item["page"]}</div>',\n                            unsafe_allow_html=True,\n                        )\n                    st.image(item["png"], use_container_width=True)\n            except Exception as locate_error:\n                st.warning("這題暫時無法自動框出完整題目，先顯示最接近的 PDF 頁面。")\n                png_bytes, shown_page, page_count = _render_pdf_page_png(url, page_number)\n                st.caption(f"PDF 第 {shown_page} / {page_count} 頁 · 定位訊息：{locate_error}")\n                st.image(png_bytes, use_container_width=True)\n        else:\n            png_bytes, shown_page, page_count = _render_pdf_page_png(url, page_number)\n            st.caption(f"PDF 第 {shown_page} / {page_count} 頁")\n            st.image(png_bytes, use_container_width=True)\n\n        clean_url = urlunsplit((*urlsplit(str(url))[:4], ""))\n        st.link_button("開啟完整官方 PDF ↗", clean_url, use_container_width=True)\n    except Exception as error:\n        st.error("原題頁面暫時無法載入，但仍可以開啟完整官方 PDF。")\n        st.caption(f"{type(error).__name__}: {error}")\n        st.link_button("開啟完整官方 PDF ↗", str(url), use_container_width=True)\n'''
if old not in text:
    raise RuntimeError('pdf viewer render block not found')
text = text.replace(old, new, 1)

app.write_text(text, encoding='utf-8')
print('added question-number crop prototype')
