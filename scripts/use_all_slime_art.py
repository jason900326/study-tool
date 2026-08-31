from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

old = '''def slime_avatar_markup(item, size="card", locked=False, mystery=False, selected=False):
    if item.get("theme") == "apple" and not mystery:
        locked_class = " locked" if locked else ""
        selected_class = " selected" if selected else ""
        art_uri = _local_asset_data_uri("assets/slimes/apple.webp")
        return (
            f'<div class="official-slime-art official-slime-art-{size}{locked_class}{selected_class}">'
            f'<img src="{art_uri}" alt="青蘋果史萊姆"></div>'
        )
'''
new = '''def slime_avatar_markup(item, size="card", locked=False, mystery=False, selected=False):
    if not mystery:
        asset_path = Path(f"assets/slimes/{item.get('theme')}.PNG")
        if asset_path.exists():
            locked_class = " locked" if locked else ""
            selected_class = " selected" if selected else ""
            art_uri = _local_asset_data_uri(asset_path)
            safe_alt = html.escape(item.get("name", "史萊姆"))
            return (
                f'<div class="official-slime-art official-slime-art-{size}{locked_class}{selected_class}">'
                f'<img src="{art_uri}" alt="{safe_alt}"></div>'
            )
'''
if old not in text:
    raise RuntimeError('slime avatar art block not found')
text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
print('all slime PNG artwork integrated')
