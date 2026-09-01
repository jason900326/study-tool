from pathlib import Path

path = Path("streamlit_app.py")
text = path.read_text(encoding="utf-8")

if "def render_quick_scroll_nav():" in text:
    raise SystemExit(0)

function_anchor = '''def gacha_page():
'''
function_insert = '''def render_quick_scroll_nav():
    st.markdown(
        """
        <div id="medslime-top"></div>
        <style>
        html { scroll-behavior:smooth; }
        .medslime-quick-nav {
            position:fixed;
            left:14px;
            bottom:calc(env(safe-area-inset-bottom, 0px) + 22px);
            z-index:999999;
            display:flex;
            flex-direction:column;
            gap:8px;
        }
        .medslime-quick-nav a {
            width:42px;
            height:42px;
            display:flex;
            align-items:center;
            justify-content:center;
            border-radius:999px;
            border:1px solid rgba(79,126,102,.22);
            background:rgba(255,255,255,.92);
            color:#315b47 !important;
            text-decoration:none !important;
            font-size:1.15rem;
            font-weight:900;
            line-height:1;
            box-shadow:0 5px 16px rgba(39,76,57,.14);
            backdrop-filter:blur(8px);
            -webkit-backdrop-filter:blur(8px);
            -webkit-tap-highlight-color:transparent;
        }
        .medslime-quick-nav a:hover {
            background:#f3faf6;
            color:#244c39 !important;
            transform:translateY(-1px);
        }
        @media (max-width:700px) {
            .medslime-quick-nav {
                left:10px;
                bottom:calc(env(safe-area-inset-bottom, 0px) + 14px);
                gap:7px;
            }
            .medslime-quick-nav a {
                width:40px;
                height:40px;
                font-size:1.08rem;
                background:rgba(255,255,255,.9);
            }
        }
        </style>
        <div class="medslime-quick-nav" aria-label="快速頁面導覽">
            <a href="#medslime-top" aria-label="回到頁面頂部" title="回到頂部">↑</a>
            <a href="#medslime-bottom" aria-label="前往頁面底部" title="前往底部">↓</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_quick_scroll_bottom():
    st.markdown('<div id="medslime-bottom" style="height:1px"></div>', unsafe_allow_html=True)


'''
if function_anchor not in text:
    raise SystemExit("Function anchor not found")
text = text.replace(function_anchor, function_insert + function_anchor, 1)

dispatch_anchor = '''page = st.session_state.medslime_page
'''
if dispatch_anchor not in text:
    raise SystemExit("Page dispatch anchor not found")
text = text.replace(dispatch_anchor, '''render_quick_scroll_nav()\n\npage = st.session_state.medslime_page\n''', 1)

end_anchor = '''else:\n    st.session_state.medslime_page = "home"\n    st.rerun()'''
if end_anchor not in text:
    raise SystemExit("Dispatch end anchor not found")
text = text.replace(end_anchor, end_anchor + '''\n\nrender_quick_scroll_bottom()''', 1)

path.write_text(text, encoding="utf-8")
