#!/usr/bin/env bash
# link-skills.sh [DEST] — link every skill of this repo into a skills folder
# (default ~/.claude/skills), so you can edit the skills in the clone while you
# use them and push improvements. Each entry is a symlink into the repo; a
# `git pull` keeps them current. Re-run after adding or renaming a skill.
#
# Never overwrites a real folder: if DEST/<name> exists and is not a link into
# this repo, it is reported and left alone. Links into this repo for skills
# that no longer exist are removed.
set -euo pipefail
REPO="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
DEST="${1:-$HOME/.claude/skills}"
mkdir -p "$DEST"
case "$(readlink -f "$DEST")" in "$REPO"|"$REPO"/*) echo "link-skills: $DEST is inside the repo; refusing" >&2; exit 1;; esac
for dir in "$REPO"/skills/*/; do
    name="$(basename "$dir")"; target="$DEST/$name"
    [[ -f "$dir/SKILL.md" ]] || continue
    if [[ -L "$target" ]]; then
        [[ "$(readlink -f "$target")" == "$(readlink -f "$dir")" ]] && { echo "ok      $name"; continue; }
        echo "skip    $name: $target links elsewhere ($(readlink "$target"))"; continue
    fi
    if [[ -e "$target" ]]; then echo "skip    $name: $target exists and is not a link"; continue; fi
    ln -s "${dir%/}" "$target"; echo "linked  $name -> ${dir%/}"
done
for link in "$DEST"/*; do
    [[ -L "$link" ]] || continue
    t="$(readlink "$link")"
    case "$t" in "$REPO"/skills/*) [[ -e "$link" ]] || { rm "$link"; echo "removed $(basename "$link") (gone from the repo)"; };; esac
done
