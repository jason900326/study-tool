from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

# Add urllib helpers.
old_import = 'import time\nfrom io import BytesIO\n'
new_import = 'import time\nfrom urllib.parse import urlsplit, urlunsplit, parse_qs\nfrom io import BytesIO\n'
if old_import not in text:
    raise RuntimeError('import anchor not found')
text = text.replace(old_import, new_import, 1)

# Insert helper functions before mistake saving section (stable utility location).
anchor = '\ndef _mistake_filter_rows(rows, source_filter):\n'
helpers = r'''
def _extract_pdf_page_hint(url):
    """Best-effort extraction of a page number from viewer/page URLs."""
    if not url:
        return None
    raw = str(url)
    patterns = [
        r"[#&?]page=(\d+)",
        r"[#&?]p=(\d+)",
        r"[#&?]pageNumber=(\d+)",
        r"/page/(\d+)(?:/|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, raw, flags=re.IGNORECASE)
        if match:
            try:
                page = int(match.group(1))
                return page if page > 0 else None
            except Exception:
                pass
    try:
        query = parse_qs(urlsplit(raw).query)
        for key in ("page", "p", "pageNumber"):
            if query.get(key):
                page = int(query[key][0])
                return page if page > 0 else None
    except Exception:
        pass
    return None


def pdf_deep_link(pdf_url, source_page_url=None, explicit_page=None):
    """Return a PDF URL that opens directly on the best known page."""
    base = str(pdf_url or source_page_url or "").strip()
    if not base:
        return ""
    page = None
    try:
        if explicit_page is not None:
            page = int(explicit_page)
    except Exception:
        page = None
    if not page:
        page = _extract_pdf_page_hint(source_page_url) or _extract_pdf_page_hint(pdf_url)
    if not page:
        return base
    try:
        parts = urlsplit(base)
        # Replace any old fragment so the page hint is deterministic.
        return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, f"page={page}"))
    except Exception:
        separator = "&" if "#" in base else "#"
        return f"{base}{separator}page={page}"

'''
if 'def pdf_deep_link(' not in text:
    if anchor not in text:
        raise RuntimeError('helper anchor not found')
    text = text.replace(anchor, '\n' + helpers + anchor.lstrip('\n'), 1)

# Keep both source URLs and compute a deep link while loading national exam questions.
old_usable = '''            "source_url": row.get("question_pdf_url") or row.get("source_page_url"),\n            "official_question_number": number,\n            "national_exam_id": row.get("id"),\n'''
new_usable = '''            "source_url": pdf_deep_link(row.get("question_pdf_url"), row.get("source_page_url")),\n            "question_pdf_url": row.get("question_pdf_url"),\n            "source_page_url": row.get("source_page_url"),\n            "source_page": _extract_pdf_page_hint(row.get("source_page_url")) or _extract_pdf_page_hint(row.get("question_pdf_url")),\n            "official_question_number": number,\n            "national_exam_id": row.get("id"),\n'''
if old_usable not in text:
    raise RuntimeError('national usable anchor not found')
text = text.replace(old_usable, new_usable, 1)

# Upgrade inline quiz link text to show page when known.
old_link = '''    if question.get("source_url"):\n        safe_url = html.escape(str(question["source_url"]), quote=True)\n        source_link = f'<a class="official-inline-link" href="{safe_url}" target="_blank" rel="noopener noreferrer">官方原題 ↗</a>'\n'''
new_link = '''    if question.get("source_url"):\n        safe_url = html.escape(str(question["source_url"]), quote=True)\n        page_hint = question.get("source_page")\n        link_label = f"官方原題 · Page {page_hint} ↗" if page_hint else "官方原題 ↗"\n        source_link = f'<a class="official-inline-link" href="{safe_url}" target="_blank" rel="noopener noreferrer">{link_label}</a>'\n'''
if old_link not in text:
    raise RuntimeError('inline source link anchor not found')
text = text.replace(old_link, new_link, 1)

# Store page hint in mistake rows so review links retain precise location.
old_row = '''            "source_url": source_url,\n        })\n'''
new_row = '''            "source_url": source_url,\n            "source_page": question.get("source_page") if source_type == "national_exam" else question.get("source_page"),\n        })\n'''
if old_row not in text:
    raise RuntimeError('mistake row anchor not found')
text = text.replace(old_row, new_row, 1)

# Make result-page link label page-aware.
old_result = '''            if question.get("source_url"):\n                st.link_button("查看官方原題 ↗", question["source_url"])\n'''
new_result = '''            if question.get("source_url"):\n                page_hint = question.get("source_page")\n                label = f"查看官方原題 · Page {page_hint} ↗" if page_hint else "查看官方原題 ↗"\n                st.link_button(label, question["source_url"])\n'''
if old_result not in text:
    raise RuntimeError('result link anchor not found')
text = text.replace(old_result, new_result, 1)

path.write_text(text, encoding='utf-8')
print('added page-aware PDF deep links')
