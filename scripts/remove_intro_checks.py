from pathlib import Path

path = Path("streamlit_app.py")
text = path.read_text(encoding="utf-8")

old = '<div class="hero-copy" style="max-width:680px;margin:.8rem auto 0">選好 PDF 後，MedSlime 會讀取教材並直接準備題目；完成後自動帶你進入第 1 題。</div><div class="check-list"><div class="check-item">✓ 題目只根據你的教材生成</div><div class="check-item">✓ 一次準備 10 題，不需要二次等待</div><div class="check-item">✓ 專有名詞保留教材原文</div><div class="check-item">✓ 每題保留教材頁碼與解析依據</div></div></div>'
new = '<div class="hero-copy" style="max-width:680px;margin:.8rem auto 0">選好 PDF 後，MedSlime 會讀取教材並直接準備題目；完成後自動帶你進入第 1 題。</div></div>'

if text.count(old) != 1:
    raise RuntimeError(f"Expected 1 intro checklist block, found {text.count(old)}")
text = text.replace(old, new, 1)

text = text.replace('    .check-list { max-width:575px; margin:1rem auto .2rem; text-align:left; display:grid; gap:.55rem; }\n', '')
text = text.replace('    .check-item { color:#315b47; font-weight:760; background:#f7fcf9; border:1px solid #e0eee6; border-radius:13px; padding:.62rem .8rem; }\n', '')

path.write_text(text, encoding="utf-8")
print("Removed intro checklist")
