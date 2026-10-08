# Source this file (do not execute it): `source tools/env.sh`
#
# - Activates the conda env that holds zotero-cli and pyzotero.
# - Loads the Zotero Web API credentials from the key file.
# - Enables hybrid mode (read via the local API, write via the Web API).
#
# Overrides: ZM_CONDA_ENV (default: zotero), ZM_KEY_FILE (default: ~/.key.secret).
# Prints nothing on success and never prints credential values.

ZM_CONDA_ENV="${ZM_CONDA_ENV:-zotero}"
ZM_KEY_FILE="${ZM_KEY_FILE:-$HOME/.key.secret}"

# Locate conda even in non-interactive shells where `conda init` has not run.
if ! command -v conda >/dev/null 2>&1; then
  for _zm_c in "${CONDA_EXE:-}" "$HOME/miniforge3/bin/conda" "$HOME/mambaforge/bin/conda" \
               "$HOME/miniconda3/bin/conda" "$HOME/anaconda3/bin/conda" \
               /opt/homebrew/Caskroom/miniforge/base/bin/conda /opt/miniconda3/bin/conda; do
    if [ -n "$_zm_c" ] && [ -x "$_zm_c" ]; then
      eval "$("$_zm_c" shell.posix hook 2>/dev/null)"
      break
    fi
  done
  unset _zm_c
fi

if command -v conda >/dev/null 2>&1; then
  if [ "${CONDA_DEFAULT_ENV:-}" != "$ZM_CONDA_ENV" ]; then
    conda activate "$ZM_CONDA_ENV" 2>/dev/null ||
      echo "tools/env.sh: conda env '$ZM_CONDA_ENV' not found. Run ./setup.sh" >&2
  fi
else
  echo "tools/env.sh: conda not found. Run ./setup.sh" >&2
fi

if [ -f "$ZM_KEY_FILE" ]; then
  . "$ZM_KEY_FILE"
else
  echo "tools/env.sh: $ZM_KEY_FILE not found; Web API writes will fail. Run ./setup.sh" >&2
fi

export ZOTERO_LOCAL="${ZOTERO_LOCAL:-true}"
export ZOTERO_LIBRARY_TYPE="${ZOTERO_LIBRARY_TYPE:-user}"
