"""Write TL;DR child notes to Zotero (SCHEMA.md §5-N).

- Input: TSV files with columns key, problem, method, result (an optional basis column is ignored).
- Each item gets exactly one child note titled `TL;DR`: updated if it exists, created otherwise.
- Other notes (arXiv auto-notes, the user's notes) and all tags are left alone.
- Reads go through the local API; writes go through the Web API (pyzotero).
  Run `source tools/env.sh` first.

usage: python tools/write_tldr.py TSV... [--apply] [--only KEY,KEY] [--lang ko|en]
"""
import argparse, csv, html, json, os, re, sys, urllib.request

LOCAL = "http://localhost:23119/api/users/0"


def local_get(path):
    out, start = [], 0
    while True:
        sep = "&" if "?" in path else "?"
        d = json.load(urllib.request.urlopen(f"{LOCAL}/{path}{sep}limit=100&start={start}"))
        out += d
        start += 100
        if len(d) < 100:
            return out


LABELS = {"ko": ("문제", "방법", "결과"), "en": ("Problem", "Method", "Result")}


def note_html(r, lang="ko"):
    lines = zip(LABELS[lang], (r["problem"], r["method"], r["result"]))
    body = "".join(f"<p>{k}: {html.escape(v.strip())}</p>" for k, v in lines)
    return f"<h1>TL;DR</h1>{body}"


def is_tldr(note):
    text = re.sub(r"<[^>]+>", "\n", note).strip()
    return text.split("\n", 1)[0].strip() == "TL;DR"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv", nargs="+")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", help="comma-separated item keys to limit the run to")
    ap.add_argument("--lang", choices=sorted(LABELS), default="ko", help="language of the line labels")
    a = ap.parse_args()

    rows = {}
    for f in a.tsv:
        for r in csv.DictReader(open(f, encoding="utf-8"), delimiter="\t"):
            rows[r["key"].strip()] = r
    if a.only:
        keep = set(a.only.split(","))
        rows = {k: v for k, v in rows.items() if k in keep}

    items = local_get("items")
    live = {i["data"]["key"] for i in items
            if i["data"]["itemType"] not in ("note", "attachment", "annotation") and not i["data"].get("deleted")}
    existing = {}
    for i in items:
        d = i["data"]
        if d["itemType"] == "note" and d.get("parentItem") and is_tldr(d["note"]):
            existing[d["parentItem"]] = d["key"]

    missing = sorted(k for k in rows if k not in live)
    creates = [k for k in rows if k in live and k not in existing]
    updates = [k for k in rows if k in live and k in existing]
    print(f"input {len(rows)} / create {len(creates)} / update {len(updates)} / not in library {len(missing)} {missing[:10]}")
    print(f"items without a TL;DR afterwards: {len(live - set(rows) - set(existing))}")
    if not a.apply:
        return

    from pyzotero import zotero
    zot = zotero.Zotero(os.environ["ZOTERO_LIBRARY_ID"], "user", os.environ["ZOTERO_API_KEY"])
    tmpl = zot.item_template("note")
    for s in range(0, len(creates), 50):
        chunk = []
        for k in creates[s:s + 50]:
            n = dict(tmpl, note=note_html(rows[k], a.lang), parentItem=k, tags=[], collections=[])
            chunk.append(n)
        res = zot.create_items(chunk)
        print(f"create {s}-{s + len(chunk)}: ok {len(res.get('successful', {}))} fail {len(res.get('failed', {}))}")
        if res.get("failed"):
            print(json.dumps(res["failed"], ensure_ascii=False)[:500])
    for k in updates:
        n = zot.item(existing[k])
        n["data"]["note"] = note_html(rows[k], a.lang)
        zot.update_item(n["data"])
    if updates:
        print(f"update {len(updates)} done")


if __name__ == "__main__":
    sys.exit(main())
