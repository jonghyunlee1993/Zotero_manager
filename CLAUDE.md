# zotero_manager

A workspace for organizing a Zotero library. Classification follows @SCHEMA.md and `ontology.yaml` (the source of truth for tags and collections). After changing classifications, run `python3 tools/check_schema.py --live`.

## Environment (automatic)
- A SessionStart hook (`.claude/settings.json` → `tools/session_start.sh`) makes every Bash command source `tools/env.sh`, which activates the conda env `zotero` and loads the Zotero credentials. `python`, `zotero-cli` and pyzotero are then available directly.
- If a command fails with `zotero-cli: command not found`, `No module named pyzotero/yaml`, or missing `ZOTERO_API_KEY`, the hook did not run: prefix the command with `source tools/env.sh && `.
- If `tools/env.sh` reports that conda, the env or the key file is missing, ask the user to run `./setup.sh` (interactive; it asks for the API key). Never ask the user to paste the key into the chat.

## First use (onboarding)
If `.is_first_setting_done` does not exist in the project root (the session hook also announces this), do this before any other library work:
1. Briefly explain that `ontology.yaml` is the original author's taxonomy (biomedical AI) and ask, with AskUserQuestion, whether to tailor it to the user's library: tailor it / keep it as is / decide later.
2. **Tailor:** launch the `ontology-tailor` subagent (`.claude/agents/ontology-tailor.md`). It reads the library and writes a proposal to `audit/onboarding/`. Show the user `proposal.md`, discuss the open questions, then replace `ontology.yaml` with the agreed version and update the tree and summaries in SCHEMA.md §1–2 to match. Offer the migration in SCHEMA.md §7 as a separate, confirmed step.
3. **Keep as is:** nothing to change.
4. In cases 2 and 3, create `.is_first_setting_done` containing the date and the choice. **Decide later:** do not create it, so the question comes back next session.

## "Triage" requests ("정리해줘")
Classify the new papers in `00_Inbox` following the procedure in SCHEMA.md §3. Show the change list first and apply only after confirmation.

## Operating rules
- Any operation that changes the library (add/edit/tags/batch/collections/delete/duplicates merge, note writes, etc.) runs **only after showing the change list and getting confirmation**. Reading is always fine.
- **Never touch the `/unread` and `/star` tags** (SCHEMA.md §3). They are automatic tags, so "Delete Automatic Tags" would remove them too.
- To show a paper in several collections, add the same item to them. Never create copies.
- When the schema changes (tree, tag vocabulary, thresholds), update `ontology.yaml` and SCHEMA.md (including the changelog) together.
- Library-specific data (paper lists, backups, drafts, reports) goes under `audit/`, which git ignores. Never put paper titles or item keys in tracked files.
- Never print API keys. Never put the user's email address or other personal data into external API requests.

## Access
- Hybrid mode: reads go through the Zotero local API, writes through the Web API (Zotero 9's local API is read-only). Web writes appear locally only after sync, so verify by polling the local API.
- CLI: `zotero-cli` (`--json` for JSON output).
- Local API: `http://localhost:23119/api/users/0/...` (the Zotero app must be running). Use it for what the CLI does not provide, such as per-tag counts (`meta.numItems` of `/tags`, which also counts notes and attachments) and each item's `collections` field.
- `zotero-cli coverage` has a small default limit; pass `--limit 100000` for everything.
- `zotero-cli get tags` sorts alphabetically. Use the local API for frequency order.
