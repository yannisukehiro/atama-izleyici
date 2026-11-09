"""Teşhis: bir sayfanın ağ isteklerini ve içeriğini loga döker."""
import json, sys
from playwright.sync_api import sync_playwright

URL = sys.argv[1]
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(locale="tr-TR", ignore_https_errors=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
    page = ctx.new_page()
    calls = []
    def on_resp(r):
        try:
            ct = r.headers.get("content-type", "")
            if r.request.resource_type in ("xhr", "fetch") or "json" in ct:
                body = r.text()
                calls.append((r.request.method, r.status, r.url, ct, len(body), body[:600]))
        except Exception as e:
            calls.append((r.request.method, r.status, r.url, "?", 0, f"okunamadı: {e}"))
    page.on("response", on_resp)
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
    print("\n=== XHR/FETCH ===")
    for c in calls:
        print(c[0], c[1], c[2], c[3], c[4])
        print("   ", c[5].replace("\n", " ")[:600])
    b.close()
