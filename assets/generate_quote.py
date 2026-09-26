#!/usr/bin/env python3
"""
generate_quote.py

Calls the Claude API to generate a motivational/inspirational quote
and writes it to quote.json, which index.html reads and displays.

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY="your-api-key-here"

Run manually:
    python3 generate_quote.py

Run on a schedule (weekly, via cron):
    Edit your crontab with `crontab -e` and add a line like:
        0 7 * * 1 /usr/bin/python3 /Users/tarafriedrich/Documents/GitHub/staracode.github.io/assets/generate_quote.py >> /Users/tarafriedrich/Documents/GitHub/staracode.github.io/assets/quote_log.txt 2>&1
    This example runs the script every Monday at 7:00 AM.

    Note: this script also commits and pushes quote.json to your GitHub repo
    so the change actually appears on the live site (GitHub Pages only serves
    what's been pushed to the repo, not local file changes). Make sure this
    machine has push access to the repo configured (SSH key or credential
    helper) so the push step can run non-interactively from cron.

    Gotcha: cron does NOT load ~/.zshrc or ~/.bash_profile, so
    ANTHROPIC_API_KEY set only in your shell profile will be invisible to
    this script when run via cron, even though it works fine when you run
    the script manually in Terminal. Either add the export directly at the
    top of your crontab (e.g. `ANTHROPIC_API_KEY=sk-ant-...`), or source
    your shell profile in the cron command itself before running python.
    If this script ever fails silently in the log with "ANTHROPIC_API_KEY
    environment variable is not set", this is almost certainly why.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone

import anthropic

# Directory containing this script, assumed to be inside the git repo
# (e.g. /Users/tarafriedrich/Documents/GitHub/staracode.github.io/assets).
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to the JSON file that index.html reads from.
# Change this if you want quote.json to live somewhere else.
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "quote.json")

# The root of the git repo, used for the commit/push step below.
# Adjust if generate_quote.py isn't one level below the repo root.
REPO_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))

PROMPT = (
    "Give me one short, original motivational or inspirational quote. "
    "It should be no more than 2 sentences, suitable for display on a website. "
    "Respond with ONLY valid JSON in this exact format, with no extra text, "
    "no markdown formatting, and no code fences:\n"
    '{"quote": "...", "author": "..."}\n'
    'If the quote is original (not attributed to a real person), '
    'set "author" to "Unknown".'
)


def generate_quote() -> dict:
    """Call the Claude API and return a dict with 'quote' and 'author'."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        messages=[{"role": "user", "content": PROMPT}],
    )

    raw_text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    ).strip()

    # Defensive cleanup in case the model wraps the JSON in code fences anyway.
    cleaned = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        print(f"ERROR: Could not parse model response as JSON:\n{raw_text}", file=sys.stderr)
        sys.exit(1)

    if "quote" not in data:
        print(f"ERROR: Model response missing 'quote' field:\n{data}", file=sys.stderr)
        sys.exit(1)

    data.setdefault("author", "Unknown")
    data["generated_at"] = datetime.now(timezone.utc).isoformat()
    return data


def write_quote(data: dict) -> None:
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Wrote new quote to {OUTPUT_PATH}: {data['quote']!r} — {data['author']}")


def commit_and_push(data: dict) -> None:
    """Commit the updated quote.json and push it so GitHub Pages picks it up.

    Cron jobs don't run inside a shell with your usual PATH or environment,
    so this uses full paths implicitly via subprocess and relies on git
    already being configured (user.name/user.email set, and push access
    via SSH key or a credential helper that doesn't require typing a
    password interactively).
    """
    rel_path = os.path.relpath(OUTPUT_PATH, REPO_DIR)
    commit_message = f"Update quote of the week ({data['generated_at']})"

    try:
        subprocess.run(["git", "add", rel_path], cwd=REPO_DIR, check=True)

        # If there's nothing new to commit (e.g. script re-run same day),
        # `git commit` exits non-zero; treat that as fine rather than fatal.
        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=REPO_DIR,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            if "nothing to commit" in (result.stdout + result.stderr).lower():
                print("No changes to commit (quote.json unchanged).")
                return
            print(f"ERROR: git commit failed:\n{result.stdout}\n{result.stderr}", file=sys.stderr)
            sys.exit(1)

        subprocess.run(["git", "push"], cwd=REPO_DIR, check=True)
        print("Committed and pushed quote.json update.")

    except subprocess.CalledProcessError as e:
        print(f"ERROR: git command failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    quote_data = generate_quote()
    write_quote(quote_data)
    commit_and_push(quote_data)