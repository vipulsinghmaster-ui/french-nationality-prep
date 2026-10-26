"""Sync the official naturalisation civic-exam question list into the dashboard.

Downloads the ministry's PDF (link discovered from the documentation page, since the
filename carries a date), extracts the questions per theme and writes
`official-questions.js` (loaded by index.html via <script>, which works from file://).
Questions keep their `first_seen` date across runs so the dashboard can flag new ones.

Usage: python scripts/sync_official_questions.py
"""
import datetime as dt
import io
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

PAGE = ("https://www.immigration.interieur.gouv.fr/documentation/guides-textes-et-brochures/"
        "questions-de-connaissance-pour-lexamen-civique-nationalite-francaise.html")
BASE = "https://www.immigration.interieur.gouv.fr"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"}
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "official-questions.js"
LOG = ROOT / "sync-log.txt"
MAX_BYTES = 20 * 1024 * 1024

THEMES = {  # PDF heading -> dashboard theme code
    "Principes et valeurs de la République": "P",
    "Système institutionnel et politique": "I",
    "Droits et devoirs": "D",
    "Histoire, géographie et culture": "H",
    "Vivre dans la société française": "V",
}


# Scheduled tasks don't inherit HTTP(S)_PROXY and urllib can't read the PAC file, so fall back to the
# local Zscaler proxy (WinHTTP default on this machine). Override with FRNAT_PROXY if it ever moves.
PROXIES = urllib.request.getproxies() or {
    k: os.environ.get("FRNAT_PROXY", "http://127.0.0.1:9000") for k in ("http", "https")}
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler(PROXIES))


def get(url: str) -> bytes:
    with OPENER.open(urllib.request.Request(url, headers=UA), timeout=60) as r:
        data = r.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise RuntimeError(f"{url} exceeds {MAX_BYTES} bytes")
    return data


def find_pdf() -> str:
    html = get(PAGE).decode("utf-8", "replace")
    links = re.findall(r'href="(/sites/dgef/files/[^"]+questions-de-connaissance[^"]*\.pdf)"', html)
    if not links:
        raise RuntimeError("PDF link not found on ministry page — layout changed?")
    return BASE + sorted(set(links))[-1]  # newest date-stamped file


def parse(text: str) -> list[dict]:
    out, theme, buf = [], None, ""
    for raw in text.splitlines():
        line = raw.replace(" ", " ").strip()
        if not line or line == "Intitulé de la question" or re.fullmatch(r"\d+", line):
            continue
        if line.rstrip(" :") in THEMES:
            theme, buf = THEMES[line.rstrip(" :")], ""
            continue
        buf = f"{buf} {line}".strip()
        # A question is complete when it ends like a prompt; otherwise it wrapped onto the next line
        if re.search(r'[?:…"»]\s*$|\.\.\.\s*$', buf):
            q = re.sub(r"\s+", " ", buf).strip()
            if theme and len(q) > 8:
                out.append({"t": theme, "q": q})
            buf = ""
    seen, uniq = set(), []
    for item in out:
        key = (item["t"], item["q"].lower())
        if key not in seen:
            seen.add(key)
            uniq.append(item)
    return uniq


def load_previous() -> dict:
    if not OUT.exists():
        return {}
    m = re.search(r"window\.OFFICIAL\s*=\s*(\{.*\});?\s*$", OUT.read_text(encoding="utf-8"), re.S)
    if not m:
        return {}
    return {q["q"]: q.get("first_seen") for q in json.loads(m.group(1)).get("questions", [])}


def main() -> int:
    import pypdf  # imported late so --help style failures stay readable

    pdf_url = find_pdf()
    reader = pypdf.PdfReader(io.BytesIO(get(pdf_url)))
    qs = parse("\n".join(p.extract_text() or "" for p in reader.pages))
    if len(qs) < 50:
        raise RuntimeError(f"only {len(qs)} questions parsed — refusing to overwrite")
    prev, today = load_previous(), dt.date.today().isoformat()
    new = [q for q in qs if q["q"] not in prev]
    for q in qs:
        q["first_seen"] = prev.get(q["q"]) or today
    removed = [k for k in prev if k not in {q["q"] for q in qs}]
    payload = {"synced": dt.datetime.now().isoformat(timespec="minutes"), "source": pdf_url, "questions": qs}
    OUT.write_text("window.OFFICIAL = " + json.dumps(payload, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
    msg = f"{payload['synced']}  {len(qs)} questions · {len(new) if prev else 0} new · {len(removed)} removed · {pdf_url}"
    with LOG.open("a", encoding="utf-8") as f:
        f.write(msg + "\n")
        for q in (new if prev else []):
            f.write(f"   + [{q['t']}] {q['q']}\n")
    print(msg)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # keep the previous official-questions.js on any failure
        with LOG.open("a", encoding="utf-8") as f:
            f.write(f"{dt.datetime.now().isoformat(timespec='minutes')}  ERROR {e}\n")
        print(f"ERROR {e}", file=sys.stderr)
        sys.exit(1)
