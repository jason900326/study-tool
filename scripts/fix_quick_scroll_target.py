from pathlib import Path

path = Path("streamlit_app.py")
text = path.read_text(encoding="utf-8")

old = '''            const button = nav.querySelector('button');
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
'''

new = '''            const button = nav.querySelector('button');
            button.textContent = '↓';
            button.setAttribute('aria-label', '前往頁面底部');
            button.title = '前往底部';

            const getScrollTarget = () => {
                const candidates = [
                    doc.querySelector('[data-testid="stAppViewContainer"]'),
                    doc.querySelector('[data-testid="stMain"]'),
                    doc.querySelector('section.main'),
                    doc.scrollingElement,
                    doc.documentElement,
                    doc.body
                ].filter(Boolean);

                let best = candidates[0] || doc.scrollingElement || doc.documentElement;
                let bestRange = -1;
                for (const el of candidates) {
                    const range = Math.max(0, (el.scrollHeight || 0) - (el.clientHeight || 0));
                    if (range > bestRange) {
                        best = el;
                        bestRange = range;
                    }
                }
                return best;
            };

            const update = () => {
                const target = getScrollTarget();
                const scrollTop = target ? (target.scrollTop || 0) : 0;
                const maxScroll = target ? Math.max(0, target.scrollHeight - target.clientHeight) : 0;

                // Only switch to ↑ when there is actually scrollable content and
                // the real Streamlit scroll container has reached its bottom.
                const atBottom = maxScroll > 4 && scrollTop >= maxScroll - 8;

                button.textContent = atBottom ? '↑' : '↓';
                button.setAttribute('aria-label', atBottom ? '回到頁面頂部' : '前往頁面底部');
                button.title = atBottom ? '回到頂部' : '前往底部';
                button.onclick = () => {
                    const liveTarget = getScrollTarget();
                    if (!liveTarget) return;
                    const liveMax = Math.max(0, liveTarget.scrollHeight - liveTarget.clientHeight);
                    const liveAtBottom = liveMax > 4 && liveTarget.scrollTop >= liveMax - 8;
                    liveTarget.scrollTo({
                        top: liveAtBottom ? 0 : liveMax,
                        behavior: 'smooth'
                    });
                };
            };

            if (win.__medslimeQuickNavBindings) {
                for (const [el, event, handler] of win.__medslimeQuickNavBindings) {
                    el.removeEventListener(event, handler);
                }
            }

            const bindings = [];
            const bind = (el, event) => {
                if (!el) return;
                el.addEventListener(event, update, {passive:true});
                bindings.push([el, event, update]);
            };

            bind(win, 'scroll');
            bind(win, 'resize');
            bind(doc.querySelector('[data-testid="stAppViewContainer"]'), 'scroll');
            bind(doc.querySelector('[data-testid="stMain"]'), 'scroll');
            bind(doc.querySelector('section.main'), 'scroll');
            bind(doc.scrollingElement, 'scroll');
            win.__medslimeQuickNavBindings = bindings;

            // Streamlit can finish laying out after this component executes.
            // Re-check a few times so the initial state is correct on first load.
            update();
            setTimeout(update, 150);
            setTimeout(update, 500);
            setTimeout(update, 1200);
'''

if old not in text:
    raise SystemExit("Current quick-scroll logic block not found")

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
