#!/usr/bin/env bash
# One-time setup for zotero_manager. Safe to re-run: every step checks first.
#
#   1. Conda: find it, or offer to install Miniforge.
#   2. Conda env: create `zotero` and install requirements.txt.
#   3. Zotero desktop: check that the local API is reachable.
#   4. Web API key: ask for it, verify it with zotero.org, store it in the key file (mode 600).
#   5. Final check.
#
# Options: --env NAME (default zotero), --key-file PATH (default ~/.key.secret), --yes (accept defaults)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
ENV_NAME="${ZM_CONDA_ENV:-zotero}"
KEY_FILE="${ZM_KEY_FILE:-$HOME/.key.secret}"
YES=0
while [ $# -gt 0 ]; do
  case "$1" in
    --env) ENV_NAME="$2"; shift 2 ;;
    --key-file) KEY_FILE="$2"; shift 2 ;;
    --yes|-y) YES=1; shift ;;
    -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

bold() { printf '\n\033[1m%s\033[0m\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$*"; }
die()  { printf '  \033[31m✗\033[0m %s\n' "$*" >&2; exit 1; }
ask()  { # ask "question" default(y|n) → returns 0 for yes
  local q="$1" d="${2:-n}" a
  if [ "$YES" = 1 ]; then [ "$d" = y ]; return; fi
  read -r -p "  $q [$( [ "$d" = y ] && echo Y/n || echo y/N )] " a || a=""
  a="${a:-$d}"; [[ "$a" =~ ^[Yy] ]]
}

# ── 1. conda ────────────────────────────────────────────────────────────
bold "1/5 conda"
find_conda() {
  command -v conda 2>/dev/null && return
  for c in "${CONDA_EXE:-}" "$HOME/miniforge3/bin/conda" "$HOME/mambaforge/bin/conda" \
           "$HOME/miniconda3/bin/conda" "$HOME/anaconda3/bin/conda" \
           /opt/homebrew/Caskroom/miniforge/base/bin/conda /opt/miniconda3/bin/conda; do
    [ -n "$c" ] && [ -x "$c" ] && { echo "$c"; return; }
  done
  return 1
}
CONDA="$(find_conda || true)"
if [ -z "$CONDA" ]; then
  warn "conda was not found."
  if ask "Install Miniforge (conda-forge's minimal conda) into ~/miniforge3?" y; then
    url="https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
    tmp="$(mktemp -d)"
    curl -fsSL "$url" -o "$tmp/miniforge.sh" || die "download failed: $url"
    bash "$tmp/miniforge.sh" -b -p "$HOME/miniforge3"
    rm -rf "$tmp"
    CONDA="$HOME/miniforge3/bin/conda"
    shell_name="$(basename "${SHELL:-bash}")"
    if ask "Run 'conda init $shell_name' so new terminals can use conda?" y; then
      "$CONDA" init "$shell_name" >/dev/null && ok "conda init $shell_name (open a new terminal to use it)"
    fi
  else
    die "conda is required. Install Miniforge or Miniconda, then re-run ./setup.sh"
  fi
fi
ok "conda: $CONDA"
eval "$("$CONDA" shell.bash hook)"

# ── 2. conda env ────────────────────────────────────────────────────────
bold "2/5 conda env '$ENV_NAME'"
if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  ok "env exists"
else
  conda create -y -q -n "$ENV_NAME" python=3.11 >/dev/null
  ok "env created (python 3.11)"
fi
conda activate "$ENV_NAME"
python -m pip install -q -r "$ROOT/requirements.txt"
command -v zotero-cli >/dev/null || die "zotero-cli is missing after install"
ok "requirements installed ($(python --version), zotero-cli)"

# ── 3. Zotero desktop / local API ───────────────────────────────────────
bold "3/5 Zotero desktop (local API)"
if curl -fs -m 3 "http://localhost:23119/api/users/0/items/top?limit=1" >/dev/null; then
  ok "local API reachable at localhost:23119"
else
  warn "local API not reachable. Start Zotero 7+ and enable"
  warn "  Settings → Advanced → 'Allow other applications on this computer to communicate with Zotero'"
  warn "Reads need this. Continuing with the rest of the setup."
fi

# ── 4. Web API key ──────────────────────────────────────────────────────
bold "4/5 Zotero Web API key → $KEY_FILE"
# check_key KEY → prints "userID write" on success
check_key() {
  ZM_K="$1" python - <<'PY'
import json, os, sys, urllib.request
req = urllib.request.Request("https://api.zotero.org/keys/current",
                             headers={"Zotero-API-Key": os.environ["ZM_K"], "Zotero-API-Version": "3"})
try:
    d = json.load(urllib.request.urlopen(req, timeout=15))
except Exception as e:
    print(f"error {e}"); sys.exit(1)
lib = d.get("access", {}).get("user", {})
print(d.get("userID"), "write" if lib.get("write") else "readonly", "notes" if lib.get("notes") else "nonotes")
PY
}

have_key=0
if [ -f "$KEY_FILE" ] && grep -q '^export ZOTERO_API_KEY=' "$KEY_FILE"; then
  have_key=1
  ok "a key is already stored"
  if ask "Replace the stored key?" n; then have_key=0; fi
fi

if [ "$have_key" = 0 ]; then
  cat <<'EOF'
  Create a key at https://www.zotero.org/settings/keys/new with:
    - Personal Library: "Allow library access", "Allow notes access", "Allow write access"
  Your userID is shown on the same page ("Your user ID for use in API calls is ...").
EOF
  [ "$YES" = 1 ] && die "--yes cannot enter a key; run without --yes"
  read -r -s -p "  Paste the API key (input hidden): " KEY; echo
  [ -n "$KEY" ] || die "empty key"
  read -r -p "  Your userID (number): " LIBID
  [[ "$LIBID" =~ ^[0-9]+$ ]] || die "userID must be a number"
  set -- $(check_key "$KEY") || true
  [ "${1:-}" = "$LIBID" ] || die "key check failed or belongs to another user (got: ${1:-?} ${2:-})"
  [ "${2:-}" = write ] || die "the key has no write access; edit it on zotero.org"
  [ "${3:-}" = notes ] || warn "the key has no notes access; TL;DR notes will fail"
  ok "key verified for user $LIBID (write access)"

  umask 077
  touch "$KEY_FILE"
  tmp="$(mktemp)"
  grep -v -E '^export (ZOTERO_API_KEY|ZOTERO_LIBRARY_ID|ZOTERO_LOCAL)=' "$KEY_FILE" > "$tmp" || true
  {
    cat "$tmp"
    echo "# zotero_manager (written by setup.sh). Keep this file mode 600 and out of synced folders/git."
    echo "export ZOTERO_API_KEY='$KEY'"
    echo "export ZOTERO_LIBRARY_ID='$LIBID'"
    echo "export ZOTERO_LOCAL=true"
  } > "$KEY_FILE"
  rm -f "$tmp"
  unset KEY
fi
chmod 600 "$KEY_FILE"
ok "key file mode 600"

# ── 5. final check ──────────────────────────────────────────────────────
bold "5/5 final check"
# shellcheck disable=SC1091
source "$ROOT/tools/env.sh"
set -- $(check_key "$ZOTERO_API_KEY") || true
if [ "${1:-}" = "$ZOTERO_LIBRARY_ID" ] && [ "${2:-}" = write ]; then
  ok "Web API: key valid for library $ZOTERO_LIBRARY_ID with write access"
else
  warn "Web API check failed (${1:-?} ${2:-}). Re-run ./setup.sh and replace the key."
fi
python -c "import yaml; yaml.safe_load(open('$ROOT/ontology.yaml'))" && ok "ontology.yaml parses"

cat <<EOF

Done. Next:
  - In a terminal:  source tools/env.sh   (then zotero-cli / python tools/... work)
  - With Claude Code: open this folder with 'claude'. The session hook loads the env automatically.
EOF
if [ ! -f "$ROOT/.is_first_setting_done" ]; then
  echo "  - First session: Claude will offer to tailor ontology.yaml to your library."
fi
