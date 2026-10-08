#!/usr/bin/env python3
"""Check classifications against ontology.yaml (read-only).

usage:
  python tools/check_schema.py --draft audit/<date>/*_classification.tsv   # check a draft TSV
  python tools/check_schema.py --live            # check the live library via the Zotero local API (GET only)
options: --ontology PATH, --out REPORT.md, --mapped OUT.tsv (save the draft converted to canonical tags)
Exit status is 1 when any per-item error is found.
"""
import argparse, csv, collections as C, json, re, sys, urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TAG_RE = re.compile(r"^(m|d|t|type|a):(\d{2})(\d{2}) (.+)$")
MODEL_RE = re.compile(r"^model:\S+$")
API = "http://localhost:23119/api/users/0"


# ── ontology ────────────────────────────────────────────────
class Ontology:
    def __init__(self, path):
        o = yaml.safe_load(open(path))
        self.raw = o
        self.version = o["version"]
        self.protected = set(o["protected_tags"])
        self.limits = o["limits"]
        self.defaults = {k: set(v) for k, v in o["defaults"].items()}
        self.leaf, self.groups, self.by_name = {}, {}, {}
        for ax, axd in o["axes"].items():
            for gg, g in axd["groups"].items():
                self.groups[f"{ax}:{gg}00 {g['name']}"] = (ax, gg)
                for ll, t in g["tags"].items():
                    full = f"{ax}:{gg}{ll} {t['name']}"
                    self.leaf[full] = dict(axis=ax, group=g["name"], name=t["name"],
                                           status=t.get("status", "active"))
                    self.by_name[f"{ax}:{t['name']}"] = full
        la = o.get("legacy_aliases", {})
        self.tag_alias = la.get("tags", {}) or {}
        self.coll_alias = la.get("collections", {}) or {}
        # collections: leaf → domain
        self.coll_leaf, self.projects = {}, set()
        for dom, dd in o["collections"].items():
            if dd.get("role") == "projects":
                self.projects |= set(dd.get("children", []))
                continue
            kids = dd.get("children")
            if kids:
                for leaf in kids:
                    self.coll_leaf[leaf] = dom
            else:
                self.coll_leaf[dom] = dom
        self.general = {c for c in self.coll_leaf if re.match(r"^\d9_", c)}
        self.reviews = o.get("reviews", []) or []
        self.model_limit = ((o.get("open_axes") or {}).get("model") or {}).get("limit", [0, 2])[1]
        self.inbox = o.get("inbox")

    def norm_tag(self, raw):
        """raw tag → (canonical tag | None, status). status: ok|alias|dropped|unknown|group|protected|model"""
        t = raw.strip().lstrip("+").strip()
        if not t:
            return None, "empty"
        if t in self.protected:
            return t, "protected"
        if MODEL_RE.match(t):
            return t, "model"
        if t in self.leaf:
            return t, "ok"
        if t in self.groups:
            return t, "group"
        if t in self.by_name:
            return self.by_name[t], "ok"
        if t in self.tag_alias:
            v = self.tag_alias[t]
            return (v, "alias") if v else (None, "dropped")
        return t, "unknown"

    def norm_coll(self, c):
        c = c.strip()
        return self.coll_alias.get(c, c)


# ── input ────────────────────────────────────────────────────
def load_draft(paths):
    items = []
    for p in paths:
        for r in csv.DictReader(open(p), delimiter="\t"):
            raw = []
            if "tags" in r:      # current format: canonical tags separated by " | "
                raw = [x for x in (r.get("tags") or "").split("|") if x.strip()]
            for col in ("m_tags", "d_tags", "t_tags", "type_tag"):
                raw += [x for x in re.split(r"[,;|]", r.get(col) or "") if x.strip()]
            items.append(dict(key=r["key"], title=r.get("short_title", ""), homes=[r["home_collection"].strip()],
                              projects=[], raw_tags=raw, fit=(r.get("fit") or "").strip(), src=Path(p).name))
    return items


def api_get(path):
    out, start = [], 0
    while True:
        sep = "&" if "?" in path else "?"
        with urllib.request.urlopen(f"{API}/{path}{sep}limit=100&start={start}") as r:
            batch = json.load(r)
            total = int(r.headers.get("Total-Results", len(batch)))
        out += batch
        start += 100
        if start >= total or not batch:
            return out


def load_live(ont):
    cols = {c["key"]: c["data"] for c in api_get("collections")}
    def name_path(k):
        p = []
        while k and k in cols:
            p.append(cols[k]["name"]); k = cols[k]["parentCollection"] or None
        return list(reversed(p))
    items = []
    for it in api_get("items/top"):
        d = it["data"]
        if d["itemType"] in ("attachment", "note"):
            continue
        homes, projects, inbox = [], [], False
        for k in d.get("collections", []):
            p = name_path(k)
            if not p:
                continue
            if p[0].startswith("_old"):      # skip an old tree archived during a migration
                continue
            if ont.inbox and p[0] == ont.inbox:
                projects.append(p[0]); inbox = True
                continue
            (projects if p[0] == "00_Projects" else homes).append(p[-1])
        tags = [t["tag"] for t in d.get("tags", [])]
        items.append(dict(key=it["key"], title=d.get("title", "")[:60], homes=homes, projects=projects,
                          raw_tags=[t for t in tags if TAG_RE.match(t) or MODEL_RE.match(t) or t in ont.protected],
                          legacy=[t for t in tags if not (TAG_RE.match(t) or MODEL_RE.match(t)) and t not in ont.protected],
                          inbox=inbox,
                          fit="", src="live"))
    return items


# ── checks ────────────────────────────────────────────────────
def check(ont, items, live=False):
    err, warn, info = C.defaultdict(list), C.defaultdict(list), C.Counter()
    usage, dom_n, dom_tag, leaf_n = C.Counter(), C.Counter(), C.defaultdict(C.Counter), C.Counter()
    mapped, cand = [], C.Counter()
    for it in items:
        k = it["key"]
        homes = [ont.norm_coll(h) for h in it["homes"]]
        if it.get("inbox"):
            if homes:
                err["E7 has a home collection but is still in the Inbox"].append(f"{k} {homes}")
            else:
                info["awaiting Inbox triage"] += 1; continue
        if homes == ["(exclude)"]:
            info["excluded"] += 1; continue
        if len(homes) != 1:
            err["E1 not exactly one home collection"].append(f"{k} {homes}")
        home = homes[0] if homes else None
        if home and home not in ont.coll_leaf:
            err["E2 collection missing or not a leaf"].append(f"{k} {home}")
        dom = ont.coll_leaf.get(home)
        tags, models = [], []
        for raw in it["raw_tags"]:
            t, st = ont.norm_tag(raw)
            if st == "protected":
                continue
            if st == "model":
                models.append(t); continue
            if st == "alias":
                info["converted via alias"] += 1
            elif st == "dropped":
                info["dropped legacy tags"] += 1; continue
            elif st == "unknown":
                err["E3 tag not in the vocabulary"].append(f"{k} {raw.strip()}"); cand[t] += 1; continue
            elif st == "group":
                err["E4 group code used as a tag"].append(f"{k} {t}"); continue
            if t in ont.defaults.get(dom, ()):
                info["domain-default tags omitted (T5)"] += 1; continue
            if t not in tags:
                tags.append(t)
        if len(models) > ont.model_limit:
            err[f"E5 more than {ont.model_limit} model: tags"].append(f"{k} {models}")
        if models:
            info["model: tags"] += len(models)
        per_axis = C.Counter(ont.leaf[t]["axis"] for t in tags)
        implied = len(ont.defaults.get(dom, ()))
        for ax, lim in ont.limits.items():
            if not isinstance(lim, list):
                continue
            hi = lim[1]
            if per_axis[ax] > hi:
                err[f"E5 more than {hi} {ax}: tags"].append(f"{k} {[t for t in tags if ont.leaf[t]['axis']==ax]}")
        if sum(per_axis.values()) + implied < ont.limits.get("min_total", 1):
            err["E6 no tags at all (defaults included)"].append(f"{k} {it['title']}")
        if live and it.get("legacy"):
            info["items with non-schema tags"] += 1
        for t in tags:
            usage[t] += 1
            if dom:
                dom_tag[dom][t] += 1
        if dom:
            dom_n[dom] += 1; leaf_n[home] += 1
        mapped.append(dict(key=k, title=it["title"], home=home, tags=" | ".join(tags), fit=it["fit"]))

    # aggregate rules
    agg = C.defaultdict(list)
    for leaf, n in sorted(leaf_n.items()):
        if n >= 80:
            agg["C1 consider splitting (leaf ≥ 80)"].append(f"{leaf}: {n}")
        if n < 5 and leaf not in ont.general:
            agg["C3 merge candidate (leaf < 5; check 3-month grace period)"].append(f"{leaf}: {n}")
    for leaf in ont.coll_leaf:
        if leaf_n[leaf] == 0:
            agg["C3 empty collection"].append(leaf)
    for g in sorted(ont.general):
        dom = ont.coll_leaf[g]
        if dom_n[dom] and leaf_n[g] / dom_n[dom] > 0.15:
            agg["C2 General share > 15%"].append(f"{g}: {leaf_n[g]}/{dom_n[dom]} = {leaf_n[g]/dom_n[dom]:.0%}")
    nonefit = [m["key"] for m in mapped if m["fit"] == "none"]
    if nonefit:
        agg["C4 no fitting collection (fit=none)"].append(f"{len(nonefit)} items: {', '.join(nonefit)}")
    for t, n in usage.most_common():
        if n >= 40:
            agg["T2 consider promoting to a group (tag ≥ 40)"].append(f"{t}: {n}")
    default_tags = set().union(*ont.defaults.values())
    for t, meta in ont.leaf.items():
        n = usage[t]
        if t in default_tags:
            continue
        if n < 3 and meta["status"] == "active":
            agg["T3 rarely used tag (< 3; judge after 6 months)"].append(f"{t}: {n}")
        if n < 3 and meta["status"] == "user-exception":
            agg["user-exception tag usage (for reference)"].append(f"{t}: {n}")
    for dom, cnt in dom_tag.items():
        for t, n in cnt.items():
            if dom_n[dom] >= 10 and n / dom_n[dom] >= 0.7:
                agg["T5 domain-default candidate (≥ 70% of domain)"].append(f"{dom} / {t}: {n}/{dom_n[dom]}")
    if cand:
        agg["candidate tags (outside the vocabulary, for T1)"] = [f"{t}: {n}" for t, n in cand.most_common() if n >= 2] + \
            [f"{sum(1 for n in cand.values() if n == 1)} more used on a single item"]
    return err, warn, info, agg, usage, leaf_n, mapped


def annotate(ont, rule_key, line):
    rule = rule_key.split()[0]
    for r in ont.reviews:
        if r["rule"] == rule and line.startswith(str(r["target"])):
            return f"{line}  ← recorded: {r['result']} ({r['date']}) {r['reason']}"
    return line


def report(ont, items, err, info, agg, usage, leaf_n, mode):
    L = [f"# Schema check report (ontology v{ont.version}, {mode})", "",
         f"- items checked: {len(items)}  /  per-item errors: {sum(len(v) for v in err.values())}"]
    L += [f"- {k}: {v}" for k, v in info.items()]
    L += ["", "## Per-item errors"]
    if not err:
        L.append("None")
    for k in sorted(err):
        v = err[k]
        L.append(f"### {k} ({len(v)})")
        L += [f"- {x}" for x in v[:40]] + ([f"- … and {len(v)-40} more"] if len(v) > 40 else [])
    L += ["", "## Aggregate rules"]
    for k in sorted(agg):
        L.append(f"### {k}")
        L += [f"- {annotate(ont, k, x)}" for x in agg[k]]
    L += ["", "## Items per collection"] + [f"- {c}: {n}" for c, n in sorted(leaf_n.items())]
    L += ["", "## Tag usage"] + [f"- {t}: {n}" for t, n in usage.most_common()]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ontology", default=ROOT / "ontology.yaml")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--draft", nargs="+")
    g.add_argument("--live", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--mapped")
    a = ap.parse_args()
    ont = Ontology(a.ontology)
    items = load_draft(a.draft) if a.draft else load_live(ont)
    err, _, info, agg, usage, leaf_n, mapped = check(ont, items, live=a.live)
    md = report(ont, items, err, info, agg, usage, leaf_n, "live" if a.live else "draft")
    if a.out:
        Path(a.out).write_text(md)
    else:
        sys.stdout.write(md)
    if a.mapped:
        with open(a.mapped, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["key", "title", "home", "tags", "fit"], delimiter="\t")
            w.writeheader(); w.writerows(mapped)
    sys.exit(1 if err else 0)


if __name__ == "__main__":
    main()
