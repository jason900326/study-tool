from pathlib import Path

path = Path("streamlit_app.py")
text = path.read_text(encoding="utf-8")

old_desktop = "bottom:calc(env(safe-area-inset-bottom, 0px) + 22px);"
new_desktop = "bottom:calc(env(safe-area-inset-bottom, 0px) + 80px);"
old_mobile = "bottom:calc(env(safe-area-inset-bottom, 0px) + 14px);"
new_mobile = "bottom:calc(env(safe-area-inset-bottom, 0px) + 90px);"

if old_desktop not in text or old_mobile not in text:
    raise SystemExit("Expected quick-nav offsets not found")

text = text.replace(old_desktop, new_desktop, 1)
text = text.replace(old_mobile, new_mobile, 1)
path.write_text(text, encoding="utf-8")
