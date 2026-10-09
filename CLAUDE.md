# zotero_manager

A workspace for organizing a Zotero library. Classification follows @SCHEMA.md and `ontology.yaml` (the source of truth for tags and collections).

The working method (repo location, conda env, where the rules are, triage and other procedures, safety rules) lives in the **`zotero-manager` skill**: `.claude/skills/zotero-manager/SKILL.md`. Use that skill for any library work. It is symlinked to `~/.claude/skills/zotero-manager`, so it also works outside this folder.

## First use (onboarding)
If `.is_first_setting_done` does not exist in the project root (the session hook also announces this), do this before any other library work:
1. Briefly explain that `ontology.yaml` is the original author's taxonomy (biomedical AI) and ask, with AskUserQuestion, whether to tailor it to the user's library: tailor it / keep it as is / decide later.
2. **Tailor:** launch the `ontology-tailor` subagent (`.claude/agents/ontology-tailor.md`). It reads the library and writes a proposal to `audit/onboarding/`. Show the user `proposal.md`, discuss the open questions, then replace `ontology.yaml` with the agreed version and update the tree and summaries in SCHEMA.md §1–2 to match. Offer the migration in SCHEMA.md §7 as a separate, confirmed step.
3. **Keep as is:** nothing to change.
4. In cases 2 and 3, create `.is_first_setting_done` containing the date and the choice. **Decide later:** do not create it, so the question comes back next session.

## Always
- Library changes only after showing the change list and getting confirmation.
- Never touch the `/unread` and `/star` tags.
- Never print API keys or send personal data to external APIs.
- Library-specific data goes under `audit/` (git-ignored).
