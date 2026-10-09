---
name: zotero-manager
description: |
  Manage the user's Zotero library with the zotero_manager taxonomy: triage the 00_Inbox
  ("정리해줘", "triage"), classify papers into home collections and tags, merge duplicates,
  replace preprints with published versions, write TL;DR notes, check the schema, or change
  the ontology. Use for any Zotero collection/tag/note work, from any working directory.
---

# zotero-manager

Works the same from any directory. The repo holds the rules and tools; this skill only says where they are and how to run them.

## 1. Locate the repo

```bash
ZM_ROOT="${ZM_ROOT:-$HOME/Workspace/zotero_manager}"
[ -f "$ZM_ROOT/ontology.yaml" ] || ZM_ROOT="$HOME/Library/Mobile Documents/com~apple~CloudDocs/Workspace/zotero_manager"
```

- `~/Workspace` is a symlink to the iCloud `Workspace` folder, so both paths are the same checkout.
- If neither exists, ask the user where the repo is. Do not clone a new one.
- Run every command below with `"$ZM_ROOT"` as the working directory (`cd "$ZM_ROOT"`), because the tools use relative paths such as `audit/`.

## 2. Environment (conda `zotero`)

Inside the repo, a SessionStart hook already sources `tools/env.sh`. From any other directory it did not run, so prefix commands:

```bash
source "$ZM_ROOT/tools/env.sh" && cd "$ZM_ROOT" && <command>
```

`tools/env.sh` activates conda env `zotero`, loads the API key from `~/.key.secret`, and sets hybrid mode (`ZOTERO_LOCAL=true`). After it, `python`, `zotero-cli` and `pyzotero` work. Overrides: `ZM_CONDA_ENV`, `ZM_KEY_FILE`.

- Message `conda not found`, `env 'zotero' not found` or `~/.key.secret not found` → ask the user to run `"$ZM_ROOT/setup.sh"` (interactive). Never ask for the API key in chat and never print it.
- Zotero desktop must be running (local API at `http://localhost:23119/api/users/0/...`).

## 3. Where the rules are (read them, do not rely on memory)

Read these from `$ZM_ROOT` at the start of a task. They change; this skill does not copy them.

| File | Content |
|---|---|
| `CLAUDE.md` | Repo instructions (not auto-loaded outside the repo, so read it) |
| `SCHEMA.md` | Principles, boundary rules, tag rules (H1, T1–T5), collection rules (C1–C5), triage procedure (§3), notes (§5), checker (§6), migration (§7) |
| `ontology.yaml` | Source of truth: tag vocabulary, parent tags, collection tree and scopes, domain defaults, labs, recorded `reviews` |
| `tools/check_schema.py` | Read-only checker (`--draft` for a TSV, `--live` for the library) |
| `tools/write_tldr.py` | Creates or updates `TL;DR` notes from TSV drafts |
| `audit/` | Library-specific drafts, backups, reports. Git-ignored |

First check that `$ZM_ROOT/.is_first_setting_done` exists. If not, run the onboarding described in `CLAUDE.md` ("First use") before other work.

## 4. How to work

1. **Read before acting.** Load `SCHEMA.md` and `ontology.yaml`, then inspect the library (read-only).
2. **Draft, show, confirm, apply.** Any write (add, edit, tags, collections, delete, duplicates merge, note writes, batch) happens only after showing the change list and getting the user's confirmation. Reading is always fine.
3. **Verify.** After applying, run `python tools/check_schema.py --live` and report errors honestly. Web API writes show up in the local API only after sync, so poll the local API to confirm.
4. **Keep data out of git.** Drafts, backups and reports go under `$ZM_ROOT/audit/<date>_<step>/`. Never put paper titles or item keys in tracked files.
5. **Change schema and docs together.** A change to the tree, vocabulary or thresholds updates `ontology.yaml` and `SCHEMA.md` (including its changelog) in the same change.

Hard rules:
- Never touch `/unread` or `/star` (no add, remove, rename, delete; exclude them from bulk operations; never use "Delete Automatic Tags"). Duplicate-merge handling is in `SCHEMA.md` §3.
- One home collection per paper (leaf only). To show a paper elsewhere, add the same item to the other collection. Never create copies.
- Never apply a tag that is not in `ontology.yaml`.
- Never send the user's email or other personal data to external APIs.

## 5. Common requests

**Triage ("정리해줘", "triage the inbox")** — follow `SCHEMA.md` §3: for each `00_Inbox` paper read title/abstract, choose one home collection, tags (child tag + parent tag) and any `model:` / `lab:` tags, draft the TL;DR, check duplicates and preprint→published, show the list, apply after confirmation, then remove from the Inbox.

**Schema check / quarterly review** — `python tools/check_schema.py --live --out report.md`, judge every flagged item against `SCHEMA.md` §4, record deliberate deferrals under `reviews` in `ontology.yaml`.

**TL;DR notes** — draft a TSV (`key, problem, method, result`, plus `basis`) under `audit/`, then `python tools/write_tldr.py <TSV> --lang ko` (dry run) and `--apply` after confirmation. The library uses Korean labels.

**Ontology change / migration** — `SCHEMA.md` §4 and §7; use the `ontology-tailor` agent only for drafting a new ontology from the library.

## 6. Access cheat sheet

- Reads: local API. Writes: Web API (Zotero 9's local API is read-only).
- CLI: `zotero-cli` (`--json` for JSON). `zotero-cli coverage` needs `--limit 100000` for everything. `zotero-cli get tags` is alphabetical; use the local API `/tags` for frequency (`meta.numItems` also counts notes and attachments).
- Each item's `collections` field is available from the local API only.
