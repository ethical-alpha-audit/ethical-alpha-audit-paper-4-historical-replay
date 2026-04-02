"""Generate code-collapsed HTML exports for academic readers.

Reads executed notebooks from the notebook plan and produces static
HTML files with code cells hidden via --no-input. Follows Rule 9 of
'Ten Simple Rules for Reproducible Research in Jupyter Notebooks'.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parents[1]
HTML_DIR = BASE_DIR / "docs" / "html"

BANNER = """<div style="background:#fff3cd;border:1px solid #ffc107;padding:0.8em 1em;border-radius:4px;margin-bottom:1.5em;font-size:0.9em">
<strong>Archival static export</strong> &mdash; generated from <code>{notebook}</code>
on {date}. Code cells are hidden for readability.
For full computational detail, open the source notebook.
For cryptographic validation, run <code>python reproduce_all.py</code>.
</div>
"""


def export_notebook(nb_path, html_path):
    """Convert a single notebook to code-collapsed HTML."""
    result = subprocess.run(
        [sys.executable, "-m", "nbconvert", "--to", "html",
         "--no-input", str(nb_path), "--output", str(html_path.resolve())],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  WARN: nbconvert failed for {nb_path.name}: {result.stderr[:200]}")
        return False

    # Inject archival banner after <body>
    content = html_path.read_text(encoding="utf-8")
    banner = BANNER.format(
        notebook=nb_path.name,
        date=datetime.now(timezone.utc).strftime("%Y-%m-%d")
    )
    content = content.replace("<body>", f"<body>\n{banner}", 1)
    html_path.write_text(content, encoding="utf-8")
    return True


def main():
    plan = json.loads(
        (BASE_DIR / "config" / "notebook_plan.json").read_text(encoding="utf-8")
    )
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    exported = 0
    for entry in plan["execution_order"]:
        nb_path = BASE_DIR / entry["path"]
        html_name = nb_path.stem + ".html"
        html_path = HTML_DIR / html_name
        if export_notebook(nb_path, html_path):
            exported += 1
            print(f"  OK: {html_name}")
        else:
            print(f"  SKIP: {html_name}")
    print(f"Exported {exported}/{len(plan['execution_order'])} notebooks to HTML")


if __name__ == "__main__":
    main()
