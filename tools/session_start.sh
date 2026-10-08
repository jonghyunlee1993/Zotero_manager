#!/usr/bin/env bash
# Claude Code SessionStart hook (registered in .claude/settings.json).
#
# 1. Makes every Bash command of the session run inside the conda env with the
#    Zotero credentials loaded, by sourcing tools/env.sh from CLAUDE_ENV_FILE.
# 2. On first use (no .is_first_setting_done), tells the agent to run onboarding.
#
# Whatever this hook prints to stdout is added to the agent's context.

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"

if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  printf 'source "%s/tools/env.sh"\n' "$ROOT" >> "$CLAUDE_ENV_FILE"
fi

if [ ! -f "$ROOT/.is_first_setting_done" ]; then
  cat <<'EOF'
[zotero_manager] First use in this checkout: `.is_first_setting_done` does not exist.
Before any other library work, run the onboarding in CLAUDE.md ("First use"):
ask the user whether to tailor ontology.yaml to their own library.
EOF
fi
exit 0
