"""Teşhis: bir sayfanın ağ isteklerini ve içeriğini loga döker."""
import json, os, sys
from playwright.sync_api import sync_playwright

URL = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge") if os.environ.get("USE_EDGE") else p.chromium.launch()
    ctx = b.new_context(locale="tr-TR", ignore_https_errors=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
    page = ctx.new_page()
    calls = []
    def on_resp(r):
        try:
            ct = r.headers.get("content-type", "")
            if r.request.resource_type in ("xhr", "fetch") or "json" in ct:
                body = r.text()
                lim = 4000 if "api" in r.url and "google" not in r.url else 400
                calls.append((r.request.method, r.status, r.url, ct, len(body), body[:lim]))
                if "api" in r.url and "google" not in r.url:
                    print("API_POST_DATA:", (r.request.post_data or "")[:500])
        except Exception as e:
            calls.append((r.request.method, r.status, r.url, "?", 0, f"okunamadı: {e}"))
    page.on("response", on_resp)
    allreq = []
    page.on("request", lambda r: allreq.append((r.method, r.resource_type, r.url)))
    page.on("console", lambda m: print("CONSOLE:", m.type, m.text[:200]))
    page.on("requestfailed", lambda r: print("REQFAILED:", r.url[:160], r.failure))
    page.goto(URL, wait_until="domcontentloaded", timeout=90000)
    try: page.wait_for_load_state("networkidle", timeout=30000)
    except Exception: pass
    page.wait_for_timeout(5000)
    print("FINAL_URL:", page.url)
    print("TITLE:", page.title())
    txt = page.inner_text("body")
    print("BODY_TEXT_LEN:", len(txt))
    print("BODY_TEXT_START:\n", txt[:1500])
    print("LINKS:", page.evaluate("document.querySelectorAll('a[href]').length"))
    print("\n=== TÜM İSTEKLER (analytics/statik hariç) ===")
    for m, t, u in allreq:
        if any(x in u for x in ("google", "gstatic", ".png", ".jpg", ".svg", ".woff", ".css", ".ico")):
            continue
        print(m, t, u[:200])
    print("\n=== TABLO/FORM HTML ===")
    for sel in ("table", "form", "select"):
        n = page.evaluate(f"document.querySelectorAll('{sel}').length")
        print(sel, "adet:", n)
    print(page.evaluate("(document.querySelector('table')||document.body).outerHTML.slice(0,2500)"))
    print("BUTTONS:", page.evaluate("[...document.querySelectorAll('button,input[type=submit],a.btn')].map(e=>(e.innerText||e.value||'').trim()).filter(Boolean).slice(0,20)"))
    print("\n=== XHR/FETCH ===")
    for c in calls:
        print(c[0], c[1], c[2], c[3], c[4])
        print("   ", c[5].replace("\n", " ")[:4000])
    b.close()
