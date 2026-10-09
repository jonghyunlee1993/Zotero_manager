# zotero_manager

Keep a Zotero library organized with a small, explicit taxonomy and an AI agent ([Claude Code](https://claude.com/claude-code)) that does the tedious parts: classifying new papers, tagging, merging duplicates, writing TL;DR notes, and checking that everything still follows the rules.

- **One home collection per paper**, organized by *domain → problem*.
- **Everything else is a tag** in a two-level hierarchy (a child tag like `m:GAN` always comes with its parent `m:generative`): method `m:`, data `d:`, task `t:`, paper type `type:`, area `a:`, plus `model:<name>` for the model a paper proposes and `lab:<PI surname>` for listed labs whose PI is an author.
- **Rules for growing the taxonomy**: when to split or merge collections, when to add or promote tags. A checker script enforces them.
- **Safe by default**: the agent shows every change before it touches the library and never touches your `/unread` and `/star` tags.

The rules are in [SCHEMA.md](SCHEMA.md). The vocabulary and collection tree are in [ontology.yaml](ontology.yaml). The shipped ontology is the author's (biomedical AI). On first use, the agent offers to tailor it to your own library.

## Repository layout

| Path | What it is |
|---|---|
| `SCHEMA.md` | Principles and rules of the taxonomy |
| `ontology.yaml` | Source of truth: tag vocabulary, collection tree, domain defaults, recorded decisions |
| `CLAUDE.md` | Instructions for the Claude Code agent working in this folder |
| `.claude/settings.json` | Session hook that loads the environment automatically |
| `.claude/skills/zotero-manager/SKILL.md` | The `zotero-manager` skill: repo location, env, rule locations, working method. Symlink it into `~/.claude/skills/` to use it from any folder |
| `.claude/agents/ontology-tailor.md` | Subagent that drafts an ontology for your library |
| `setup.sh` | One-time setup (conda env, dependencies, API key) |
| `tools/env.sh` | `source` it to activate the env and load credentials |
| `tools/check_schema.py` | Read-only checker for drafts or the live library |
| `tools/write_tldr.py` | Creates or updates one `TL;DR` note per paper |
| `audit/` | Your library-specific drafts, backups and reports (git-ignored) |

## Requirements

- macOS or Linux, `bash`, `curl`
- [Zotero](https://www.zotero.org/) 7 or later, running, with Settings → Advanced → "Allow other applications on this computer to communicate with Zotero" enabled
- A zotero.org account with sync enabled (writes go through the Zotero Web API)
- [Claude Code](https://claude.com/claude-code) for the agent workflow (the scripts also work on their own)
- conda. If it is missing, `setup.sh` offers to install [Miniforge](https://github.com/conda-forge/miniforge).

## Setup

```bash
git clone https://github.com/jonghyunlee1993/Zotero_manager.git
cd Zotero_manager
./setup.sh
```

`setup.sh` is safe to re-run. It:

1. finds conda, or offers to install Miniforge and run `conda init`;
2. creates the conda env `zotero` (Python 3.11) and installs `requirements.txt` (`zotero-mcp-server` provides `zotero-cli`, plus `pyzotero` and `PyYAML`);
3. checks that the Zotero desktop local API answers at `localhost:23119`;
4. asks for your Zotero Web API key and userID, verifies them with zotero.org (write access required), and stores them in `~/.key.secret` with mode 600;
5. runs a final check.

**Creating the API key:** go to <https://www.zotero.org/settings/keys/new>. Under *Personal Library*, enable "Allow library access", "Allow notes access" and "Allow write access". The same page shows your userID ("Your user ID for use in API calls is …"). The key is entered with hidden input and never stored inside the repository.

Options: `./setup.sh --env NAME --key-file PATH`. The same overrides work for `tools/env.sh` through `ZM_CONDA_ENV` and `ZM_KEY_FILE`.

## Using it with Claude Code

```bash
cd Zotero_manager
claude
```

- **Environment:** the session hook sources `tools/env.sh` for every command, so the agent runs inside the conda env with your credentials loaded. You do not need to activate anything yourself.
- **First session:** `.is_first_setting_done` does not exist yet, so the agent asks whether to tailor the ontology to your library.
  - If you say yes, the `ontology-tailor` subagent reads your library (read-only) and writes a proposal to `audit/onboarding/`. You review it with the agent, and it then updates `ontology.yaml` and `SCHEMA.md`.
  - If you choose, the agent can then migrate your library step by step ([SCHEMA.md §7](SCHEMA.md#7-migrating-an-existing-library-to-this-schema)). Each step waits for your confirmation.
  - The flag file is git-ignored, so every clone runs its own onboarding.
- **Day to day:** drop new papers into `00_Inbox` and ask the agent to "triage the inbox". It proposes a home collection, tags, a TL;DR note and duplicate or preprint fixes, and applies them after you confirm.
- **Quarterly:** ask for a schema check. The agent runs the checker and proposes splits, merges or new tags according to the rules.

## Using the scripts directly

```bash
source tools/env.sh
python tools/check_schema.py --live --out report.md     # check the live library (read-only)
python tools/write_tldr.py notes.tsv --lang en          # dry run: counts only
python tools/write_tldr.py notes.tsv --lang en --apply  # create or update TL;DR notes
zotero-cli --help
```

`write_tldr.py` takes TSV files with the columns `key`, `problem`, `method` and `result`.

## How it talks to Zotero

- **Reads** go through the Zotero desktop local API (`http://localhost:23119/api/users/0/...`). Zotero must be running.
- **Writes** go through the Zotero Web API with your key (hybrid mode), because the local API of Zotero 9 is read-only. Changes reach the desktop app after the next sync. From Zotero 10 the local API can write.
- The key lives in `~/.key.secret` (mode 600), outside the repository. Do not put it in a synced folder or commit it. `.gitignore` excludes `*.secret`, `.env`, `audit/` and TSV/report files.

## Safety rules the agent follows

- Shows a change list and waits for confirmation before any write.
- Never adds, removes or renames `/unread` or `/star`, and never uses Zotero's "Delete Automatic Tags".
- Never creates duplicate items. A paper shown in several collections is the same item.
- Never modifies notes you wrote. It keeps arXiv auto-notes.
- Never sends your email address or other personal data to external APIs (Semantic Scholar, OpenAlex, bioRxiv) when it looks up published versions.
