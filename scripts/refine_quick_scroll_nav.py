from pathlib import Path

path = Path("streamlit_app.py")
text = path.read_text(encoding="utf-8")

old = '''def render_quick_scroll_nav():
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

new = '''def render_quick_scroll_nav():
    # Inject the control into Streamlit's parent document so it can react to the
    # real page scroll position. Exactly one button is visible at a time:
    # ↓ until the user reaches the bottom, then ↑.
    import streamlit.components.v1 as components

    components.html(
        """
        <script>
        (() => {
            const doc = window.parent.document;
            const win = window.parent;
            const NAV_ID = 'medslime-quick-nav';
            const STYLE_ID = 'medslime-quick-nav-style';

            let style = doc.getElementById(STYLE_ID);
            if (!style) {
                style = doc.createElement('style');
                style.id = STYLE_ID;
                style.textContent = `
                    html { scroll-behavior:smooth; }
                    #${NAV_ID} {
                        position:fixed;
                        right:14px;
                        bottom:calc(env(safe-area-inset-bottom, 0px) + 22px);
                        z-index:999999;
                    }
                    #${NAV_ID} button {
                        width:42px;
                        height:42px;
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        border-radius:999px;
                        border:1px solid rgba(79,126,102,.22);
                        background:rgba(255,255,255,.92);
                        color:#315b47;
                        font:900 1.15rem/1 system-ui,-apple-system,sans-serif;
                        box-shadow:0 5px 16px rgba(39,76,57,.14);
                        backdrop-filter:blur(8px);
                        -webkit-backdrop-filter:blur(8px);
                        -webkit-tap-highlight-color:transparent;
                        cursor:pointer;
                    }
                    #${NAV_ID} button:hover { background:#f3faf6; transform:translateY(-1px); }
                    @media (max-width:700px) {
                        #${NAV_ID} {
                            right:10px;
                            bottom:calc(env(safe-area-inset-bottom, 0px) + 14px);
                        }
                        #${NAV_ID} button {
                            width:40px;
                            height:40px;
                            font-size:1.08rem;
                            background:rgba(255,255,255,.9);
                        }
                    }
                `;
                doc.head.appendChild(style);
            }

            let nav = doc.getElementById(NAV_ID);
            if (!nav) {
                nav = doc.createElement('div');
                nav.id = NAV_ID;
                const button = doc.createElement('button');
                button.type = 'button';
                nav.appendChild(button);
                doc.body.appendChild(nav);
            }

            const button = nav.querySelector('button');
            const update = () => {
                const root = doc.documentElement;
                const body = doc.body;
                const scrollTop = win.scrollY || root.scrollTop || body.scrollTop || 0;
                const viewport = win.innerHeight || root.clientHeight;
                const fullHeight = Math.max(
                    body.scrollHeight, body.offsetHeight,
                    root.clientHeight, root.scrollHeight, root.offsetHeight
                );
                const atBottom = scrollTop + viewport >= fullHeight - 8;
                button.textContent = atBottom ? '↑' : '↓';
                button.setAttribute('aria-label', atBottom ? '回到頁面頂部' : '前往頁面底部');
                button.title = atBottom ? '回到頂部' : '前往底部';
                button.onclick = () => win.scrollTo({
                    top: atBottom ? 0 : fullHeight,
                    behavior: 'smooth'
                });
            };

            if (win.__medslimeQuickNavHandler) {
                win.removeEventListener('scroll', win.__medslimeQuickNavHandler);
                win.removeEventListener('resize', win.__medslimeQuickNavHandler);
            }
            win.__medslimeQuickNavHandler = update;
            win.addEventListener('scroll', update, {passive:true});
            win.addEventListener('resize', update, {passive:true});
            update();
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def render_quick_scroll_bottom():
    # Kept as a no-op for the existing page dispatcher.
    return
'''

if old not in text:
    raise SystemExit("Existing quick scroll block not found")

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
