#!/usr/bin/env python3
"""Kamu ilan/atama sitelerini izler, yeni bağlantı/başlık çıkınca ntfy ile telefona bildirir."""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

SITES = {
    "Kamu İlan (SBB)": "https://kamuilan.sbb.gov.tr/",
    "Kariyer Kapısı - İşe Alım": "https://kariyerkapisi.gov.tr/isealim",
    "Yerel Yönetimler (ÇŞB)": "https://yerelyonetimler.csb.gov.tr/",
}

STATE_FILE = Path("state.json")
FAIL_ALERT_THRESHOLD = 3  # üst üste bu kadar hatadan sonra haber ver

NTFY_TOPIC = os.environ["NTFY_TOPIC"].strip()
print(f"ntfy konu uzunluğu: {len(NTFY_TOPIC)}")


def notify(text: str) -> None:
    """ntfy JSON API ile gönderir (Türkçe karakter/emoji sorunu yok). Hata olursa çökmez."""
    print("BİLDİRİM:", text)
    lines = text.split("\n", 1)
    body = json.dumps(
        {
            "topic": NTFY_TOPIC,
            "title": lines[0][:120],
            "message": (lines[1] if len(lines) > 1 else lines[0])[:3500],
            "priority": 4,
        }
    ).encode("utf-8")
    try:
        req = urllib.request.Request(
            "https://ntfy.sh/",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=30).read()
    except urllib.error.HTTPError as e:
        print(f"ntfy gönderilemedi: {e} -> {e.read()[:300]!r}", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f"ntfy gönderilemedi: {e}", file=sys.stderr)


def scrape(page, url: str) -> dict:
    """Sayfadaki tüm (metin, link) çiftlerini döndürür. {anahtar: başlık}"""
    page.goto(url, wait_until="domcontentloaded", timeout=90000)
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:  # noqa: BLE001
        pass
    page.wait_for_timeout(3000)
    print(f"  [{url}] başlık={page.title()!r} uzunluk={len(page.content())}")
    items = page.evaluate(
        """() => {
          const out = [];
          document.querySelectorAll('a[href]').forEach(a => {
            const t = (a.innerText || a.title || '').trim().replace(/\\s+/g, ' ');
            if (t.length >= 8) out.push([t, a.href]);
          });
          // Tablo satırları / kart başlıkları (link olmayan ilanlar için)
          document.querySelectorAll('tr, .card, .list-group-item, li').forEach(el => {
            const t = (el.innerText || '').trim().replace(/\\s+/g, ' ');
            if (t.length >= 20 && t.length <= 300) out.push([t, '']);
          });
          return out;
        }"""
    )
    return {f"{t}||{h}": t for t, h in items}


def main() -> int:
    state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    first_run = not state
    errors = 0

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            locale="tr-TR",
            ignore_https_errors=True,
        )
        for name, url in SITES.items():
            site = state.setdefault(name, {"seen": [], "fails": 0})
            try:
                page = ctx.new_page()
                found = scrape(page, url)
                page.close()
                if not found:
                    raise RuntimeError("Sayfadan içerik okunamadı")
                site["fails"] = 0
                seen = set(site["seen"])
                new = {k: v for k, v in found.items() if k not in seen}
                if new and seen:  # ilk çalıştırmada bildirim yok, sadece kayıt
                    lines = [f"🔔 {name}: {len(new)} yeni içerik"]
                    for k, title in list(new.items())[:8]:
                        link = k.split("||", 1)[1]
                        lines.append(f"• {title[:150]}" + (f"\n  {link}" if link else ""))
                    lines.append(f"\n{url}")
                    notify("\n".join(lines))
                site["seen"] = sorted(seen | set(found))
                print(f"{name}: {len(found)} öğe, {len(new)} yeni")
            except Exception as e:  # noqa: BLE001
                errors += 1
                site["fails"] = site.get("fails", 0) + 1
                print(f"{name}: HATA {e}", file=sys.stderr)
                if site["fails"] == FAIL_ALERT_THRESHOLD:
                    notify(f"⚠️ {name} {FAIL_ALERT_THRESHOLD} kez üst üste okunamadı: {e}\n{url}")
        browser.close()

    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1))
    if first_run:
        notify("✅ Atama izleyici kuruldu. Bundan sonra yeni içerik çıkınca haber vereceğim.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
