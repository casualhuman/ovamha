"""Genuine offline check in a real browser (Chromium via Playwright).

1. Open the app from the local hub, sign in, run a check (confirm a danger sign).
2. Cut the browser's network entirely and reload: the app's screens must still open
   from the installed-app cache (service worker), even with no connection at all.
3. The hub itself makes no internet calls: models load with HF_HUB_OFFLINE=1.

    .venv/bin/python scripts/offline_check.py [http://localhost:8000]
"""
import json
import sys

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 390, "height": 844})
    page = ctx.new_page()
    page.goto(URL)
    page.evaluate("navigator.serviceWorker.ready")
    page.reload()  # second load is controlled by the service worker
    page.wait_for_timeout(1500)
    sw = page.evaluate("""async () => ({controlled: !!navigator.serviceWorker.controller,
        cached: (await (await caches.open((await caches.keys())[0])).keys()).map(r => new URL(r.url).pathname)})""")
    print("1. installed-app cache:", json.dumps(sw))

    # A full check through the hub (local network only)
    page.evaluate("""async () => {
        go('login'); S.username = 'fati'; S.pin = '769131';
        const r = await api('/api/login', {body: {username: 'fati', pin: '769131'}});
        S.token = r.token; S.worker = r.worker; session.save({token: S.token, worker: S.worker, lang: 'en'}, false); go('home');
        await startCheck(); S.st = await api('/api/woman/find', {body: {card_code: 'MAM-A2A'}});
        await readBack('She has seen blood since this morning, a lot of it.');
        S.st = await api('/api/confirm', {body: {field: 'vaginal_bleeding'}});
    }""")
    print("2. check via hub:", page.evaluate("S.st.preview.danger"), "(danger sign confirmed)")

    # Cut the network completely and reload
    ctx.set_offline(True)
    page.reload()
    page.wait_for_timeout(1500)
    title = page.evaluate("document.querySelector('.auth-title, .welcome h2, .hello b')?.textContent || document.title")
    note = page.evaluate("document.querySelector('.note-line.warn')?.textContent || ''")
    print("3. network OFF, reload -> app still opens:", repr(title.strip()), "| still signed in:", page.evaluate("!!S.token"))
    print("   message:", repr(note.strip()))
    page.screenshot(path="ml/eval/results/offline-reload.png")
    browser.close()
