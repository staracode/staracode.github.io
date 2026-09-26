#!/usr/bin/env python3
"""
update_sitemap.py

Updates the <lastmod> date in sitemap.xml to today's date, but only if
there are other staged changes in this commit (so committing unrelated
things, like just this hook itself, doesn't spuriously bump the date).

Intended to be called from a git pre-commit hook — see install_hook.sh
for setup instructions.
"""

import re
import subprocess
import sys
from datetime import date
from pathlib import Path

# Path to sitemap.xml, relative to the repo root.
SITEMAP_PATH = Path(__file__).resolve().parent / "sitemap.xml"


def get_staged_files() -> list[str]:
    """Return a list of file paths staged for this commit."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def update_lastmod(today: str) -> bool:
    """Update <lastmod> in sitemap.xml. Returns True if the file changed."""
    if not SITEMAP_PATH.exists():
        print(f"ERROR: {SITEMAP_PATH} not found.", file=sys.stderr)
        sys.exit(1)

    content = SITEMAP_PATH.read_text(encoding="utf-8")
    new_content, count = re.subn(
        r"<lastmod>\d{4}-\d{2}-\d{2}</lastmod>",
        f"<lastmod>{today}</lastmod>",
        content,
    )

    if count == 0:
        print("WARNING: No <lastmod> tag found/updated in sitemap.xml.", file=sys.stderr)
        return False

    if new_content == content:
        # Already up to date (e.g. hook ran twice same day).
        return False

    SITEMAP_PATH.write_text(new_content, encoding="utf-8")
    return True


def stage_sitemap() -> None:
    subprocess.run(["git", "add", str(SITEMAP_PATH)], check=True)


def main() -> None:
    staged = get_staged_files()
    sitemap_rel_name = SITEMAP_PATH.name

    # Only bump lastmod if something OTHER than the sitemap itself is
    # being committed — avoids an infinite "just updating the date" loop
    # and avoids bumping the date on unrelated commits that don't touch
    # any site content (e.g. only touching this script).
    other_files_staged = [f for f in staged if not f.endswith(sitemap_rel_name)]

    if not other_files_staged:
        print("No other staged changes — leaving sitemap.xml lastmod as-is.")
        return

    today = date.today().isoformat()
    changed = update_lastmod(today)

    if changed:
        stage_sitemap()
        print(f"Updated sitemap.xml lastmod to {today} and staged it.")
    else:
        print("sitemap.xml lastmod already current — nothing to do.")


if __name__ == "__main__":
    main()