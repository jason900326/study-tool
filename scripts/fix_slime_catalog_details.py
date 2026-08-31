from pathlib import Path

path = Path('streamlit_app.py')
text = path.read_text(encoding='utf-8')

emoji_map = {
    '青蘋果史萊姆': '🟢',
    '葡萄史萊姆': '🟣',
    '草莓史萊姆': '🍓',
    '檸檬史萊姆': '🟡',
    '牛奶史萊姆': '🥛',
    '蜂蜜史萊姆': '🍯',
    '咖啡史萊姆': '☕',
    '雲朵史萊姆': '☁️',
    '海洋史萊姆': '🌊',
    '晚霞史萊姆': '🌅',
    '星空史萊姆': '🌌',
}
for name, emoji in emoji_map.items():
    needle = f'{{"name": "{name}", "rarity": '
    idx = text.find(needle)
    if idx == -1:
        raise RuntimeError(f'catalog entry missing: {name}')
    line_end = text.find('\n', idx)
    line = text[idx:line_end]
    if '"emoji":' not in line:
        line_new = line.replace(f'{{"name": "{name}", ', f'{{"name": "{name}", "emoji": "{emoji}", ', 1)
        text = text[:idx] + line_new + text[line_end:]

old_css = '    .theme-strawberry { background-image:radial-gradient(circle at 28% 28%,rgba(255,235,165,.7) 0 2px,transparent 3px),radial-gradient(circle at 68% 52%,rgba(255,235,165,.65) 0 2px,transparent 3px) !important; }\n'
new_css = '    .theme-strawberry::before { content:"✦  ·  ✦"; position:absolute; left:19%; top:18%; color:rgba(255,235,165,.72); font-size:.55rem; letter-spacing:.38rem; transform:rotate(-8deg); }\n'
if old_css not in text:
    raise RuntimeError('strawberry CSS anchor not found')
text = text.replace(old_css, new_css, 1)

path.write_text(text, encoding='utf-8')
print('fixed slime catalog visual details')
