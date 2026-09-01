from pathlib import Path

path = Path("streamlit_app.py")
text = path.read_text(encoding="utf-8")

anchor = '''    .uncertain-inline-text {
        min-height:38px; display:flex; align-items:center; gap:.35rem; padding:.45rem .15rem;
        color:#244c39; line-height:1.45;
    }
'''

replacement = '''    .uncertain-inline-text {
        min-height:38px; display:flex; align-items:center; gap:.35rem; padding:.45rem .15rem;
        color:#244c39; line-height:1.45; font-size:1rem !important;
    }
    [class*="st-key-national_strike_"] button p,
    [class*="st-key-material_strike_"] button p {
        font-size:1rem !important;
    }

    /* Mobile quiz rows: keep the answer circle and option text on the same row.
       The text column uses all remaining width and wraps only when it truly needs to. */
    @media (max-width:700px) {
        [data-testid="stHorizontalBlock"]:has([class*="st-key-national_pick_wrap_"]),
        [data-testid="stHorizontalBlock"]:has([class*="st-key-material_pick_wrap_"]),
        [data-testid="stHorizontalBlock"]:has([class*="st-key-national_uncertain_pick_wrap_"]),
        [data-testid="stHorizontalBlock"]:has([class*="st-key-material_uncertain_pick_wrap_"]) {
            flex-wrap:nowrap !important;
            align-items:flex-start !important;
            gap:.35rem !important;
        }
        [data-testid="stHorizontalBlock"]:has([class*="st-key-national_pick_wrap_"]) > [data-testid="stColumn"]:first-child,
        [data-testid="stHorizontalBlock"]:has([class*="st-key-material_pick_wrap_"]) > [data-testid="stColumn"]:first-child,
        [data-testid="stHorizontalBlock"]:has([class*="st-key-national_uncertain_pick_wrap_"]) > [data-testid="stColumn"]:first-child,
        [data-testid="stHorizontalBlock"]:has([class*="st-key-material_uncertain_pick_wrap_"]) > [data-testid="stColumn"]:first-child {
            flex:0 0 44px !important;
            width:44px !important;
            min-width:44px !important;
        }
        [data-testid="stHorizontalBlock"]:has([class*="st-key-national_pick_wrap_"]) > [data-testid="stColumn"]:last-child,
        [data-testid="stHorizontalBlock"]:has([class*="st-key-material_pick_wrap_"]) > [data-testid="stColumn"]:last-child,
        [data-testid="stHorizontalBlock"]:has([class*="st-key-national_uncertain_pick_wrap_"]) > [data-testid="stColumn"]:last-child,
        [data-testid="stHorizontalBlock"]:has([class*="st-key-material_uncertain_pick_wrap_"]) > [data-testid="stColumn"]:last-child {
            flex:1 1 auto !important;
            width:auto !important;
            min-width:0 !important;
        }
    }
'''

if "Mobile quiz rows: keep the answer circle" in text:
    raise SystemExit(0)
if anchor not in text:
    raise SystemExit("Expected CSS anchor not found; refusing to patch.")

path.write_text(text.replace(anchor, replacement, 1), encoding="utf-8")
