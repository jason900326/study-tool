from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

if 'from pathlib import Path\n' not in text:
    anchor = 'from io import BytesIO\n'
    if anchor not in text:
        raise RuntimeError('import anchor not found')
    text = text.replace(anchor, anchor + 'from pathlib import Path\n', 1)

path.write_text(text, encoding='utf-8')
print('Path import fixed')
