from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

anchor = '''    [class*="st-key-mistake_folder_row_"] button p { width:100% !important; text-align:left !important; color:#244c39 !important; font-weight:800 !important; line-height:1.45 !important; white-space:normal !important; }\n'''
replacement = anchor + '''    [class*="st-key-mistake_folder_row_"] button > div,\n    [class*="st-key-mistake_folder_row_"] button [data-testid="stMarkdownContainer"] { width:100% !important; display:flex !important; justify-content:flex-start !important; text-align:left !important; }\n    [class*="st-key-mistake_folder_row_"] button span { text-align:left !important; }\n'''

if anchor not in text:
    raise RuntimeError('mistake folder alignment CSS anchor not found')
text = text.replace(anchor, replacement, 1)
path.write_text(text, encoding='utf-8')
print('left-aligned mistake folder rows')
