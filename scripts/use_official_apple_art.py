from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

if 'import base64\n' not in text:
    text = text.replace('import hashlib\n', 'import base64\nimport hashlib\n', 1)

helper_anchor = 'def slime_avatar_markup(item, size="card", locked=False, mystery=False, selected=False):\n'
helper_insert = '''def _local_asset_data_uri(asset_path):\n    with open(asset_path, "rb") as asset_file:\n        encoded = base64.b64encode(asset_file.read()).decode("ascii")\n    suffix = str(asset_path).lower().rsplit(".", 1)[-1]\n    mime = "image/webp" if suffix == "webp" else "image/png"\n    return f"data:{mime};base64,{encoded}"\n\n\ndef slime_avatar_markup(item, size="card", locked=False, mystery=False, selected=False):\n    if item.get("theme") == "apple" and not mystery:\n        locked_class = " locked" if locked else ""\n        selected_class = " selected" if selected else ""\n        art_uri = _local_asset_data_uri("assets/slimes/apple.webp")\n        return (\n            f'<div class="official-slime-art official-slime-art-{size}{locked_class}{selected_class}">'\n            f'<img src="{art_uri}" alt="青蘋果史萊姆"></div>'\n        )\n'''
if 'def _local_asset_data_uri(asset_path):' not in text:
    if helper_anchor not in text:
        raise RuntimeError('slime avatar helper anchor not found')
    text = text.replace(helper_anchor, helper_insert, 1)

css_anchor = '    .catalog-slime-home { width:150px; height:118px; margin:0 auto .8rem; animation:slimeBounce 2.4s ease-in-out infinite; }\n'
css_add = css_anchor + '''    .official-slime-art { display:flex; align-items:center; justify-content:center; overflow:hidden; border-radius:24px; }\n    .official-slime-art img { display:block; width:100%; height:100%; object-fit:contain; border-radius:inherit; }\n    .official-slime-art-card { width:154px; height:124px; margin:0 auto; }\n    .official-slime-art-home { width:190px; height:153px; margin:0 auto .45rem; animation:slimeBounce 2.4s ease-in-out infinite; }\n    .official-slime-art-hero { width:220px; height:177px; margin:0 auto; animation:slimeBounce 2.2s ease-in-out infinite; }\n    .official-slime-art.locked { filter:saturate(.42); opacity:.64; }\n'''
if '.official-slime-art {' not in text:
    if css_anchor not in text:
        raise RuntimeError('slime css anchor not found')
    text = text.replace(css_anchor, css_add, 1)

path.write_text(text, encoding='utf-8')
print('official apple artwork integrated')
