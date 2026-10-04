"""Smoke test a running MaternaSave app (hosted or local): sign in, run a Yoruba visit, check the
Yoruba guideline advice and the read-back voice. Exits non-zero on any failure.

    .venv/bin/python scripts/smoke_hosted.py                      # https://r8086-ovamha.hf.space
    .venv/bin/python scripts/smoke_hosted.py http://localhost:8000
"""
import json
import sys
import time
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://r8086-ovamha.hf.space").rstrip("/")
USER, PIN = "funmi", "186706"  # public demo account (README, "For judges")


def call(path, body=None, token=None, raw=False):
    headers = {"Content-Type": "application/json"} | ({"Authorization": f"Bearer {token}"} if token else {})
    req = urllib.request.Request(BASE + path, json.dumps(body or {}).encode() if body is not None else None, headers)
    r = urllib.request.urlopen(req, timeout=180)
    return r if raw else json.load(r)


def wait_until_up(minutes=15):
    for _ in range(minutes * 6):
        try:
            call("/api/config")
            return
        except (urllib.error.URLError, OSError):
            time.sleep(10)
    raise SystemExit(f"{BASE} did not come up within {minutes} minutes")


def check(name, ok):
    print(("PASS " if ok else "FAIL ") + name)
    return ok


def main():
    wait_until_up()
    tok = call("/api/login", {"username": USER, "pin": PIN})["token"]
    call("/api/encounter/new", {"lang": "yo"}, tok)
    call("/api/woman/find", {"card_code": "anc-24t"}, tok)
    st = call("/api/extract", {"transcript": "orin ń fọ́ gidi gidi ara rẹ̀ sín gbọ́nà", "lang": "yo"}, tok)
    found = {i["field"] for i in st["items"]}
    results = [check("Yoruba keywords: headache and fever understood", {"headache", "fever"} <= found)]
    call("/api/confirm", {"field": "headache", "value": "severe"}, tok)
    a = call("/api/finish", {}, tok)
    yo = (a.get("translations") or {}).get("yo")
    results.append(check("Yoruba guideline advice returned", bool(yo)))
    if yo:
        text = json.dumps(yo, ensure_ascii=False)
        results.append(check("Yoruba advice text present (Orí fífọ́)", "Orí fífọ́" in text))
        results.append(check("Doses unchanged in Yoruba (Aspirin 75 mg)", "75 mg" in text or not a.get("management")))
    r = call("/api/speak", {"field": "headache", "value": True, "lang": "yo"}, tok, raw=True)
    results.append(check("Yoruba read-back spoken in Yoruba", r.headers.get("X-Ovamha-Lang") == "yo"))
    if not all(results):
        raise SystemExit(f"Smoke test FAILED on {BASE}")
    print(f"All checks passed on {BASE}")


if __name__ == "__main__":
    main()
