from pathlib import Path

# Stable ASCII entry point for Streamlit Cloud.
# Keep the original learning app in 學習.py and execute it here.
source_path = Path(__file__).with_name("學習.py")
source_code = source_path.read_text(encoding="utf-8")
exec(compile(source_code, str(source_path), "exec"), {"__name__": "__main__", "__file__": str(source_path)})
