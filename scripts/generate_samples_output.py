"""Runs the three required test samples against a LIVE backend and writes their
real review output into README.md, between the SAMPLES:START/END markers.

This does NOT fabricate output — it calls POST /review/snippet for real, on
whichever OLLAMA_MODEL your backend is configured with, and writes down
exactly what came back. Run it after `make dev-backend` is up:

    uv run python scripts/generate_samples_output.py
"""

import json
import os
import re
from pathlib import Path

import httpx

ROOT = Path(__file__).parent.parent
API_URL = os.environ.get("REVIEWER_API_URL", "http://localhost:8000")
README = ROOT / "README.md"

SAMPLES = [
    ("Clean sample (expect: mostly Approve, at most minor nitpicks)", "samples/clean_sample.py"),
    ("Security issue sample (expect: Request Changes)", "samples/security_issue.py"),
    ("Logic bug sample (expect: Request Changes)", "samples/logic_bug.py"),
]

START = "<!-- SAMPLES:START -->"
END = "<!-- SAMPLES:END -->"


def review(path: Path) -> dict:
    content = path.read_text()
    resp = httpx.post(
        f"{API_URL}/review/snippet",
        json={"filename": path.name, "content": content},
        timeout=180,
    )
    resp.raise_for_status()
    return resp.json()


def render_section(title: str, relpath: str, source: str, result: dict) -> str:
    issues_md = ""
    if result["issues"]:
        rows = "\n".join(
            f"| {i.get('line') or '-'} | {i['category']} | {i['severity']} | {i['message']} | "
            f"{i.get('suggestion') or ''} |"
            for i in result["issues"]
        )
        issues_md = (
            "| Line | Category | Severity | Comment | Suggestion |\n"
            "|---|---|---|---|---|\n" + rows
        )
    else:
        issues_md = "_No issues found._"

    return f"""### {title}

**File:** `{relpath}`

```python
{source}
```

**Verdict:** {result['verdict']} \u2014 {result['justification']}

{result['summary']}

{issues_md}
"""


def main() -> None:
    sections = []
    for title, relpath in SAMPLES:
        path = ROOT / relpath
        print(f"Reviewing {relpath} ...")
        result = review(path)
        sections.append(render_section(title, relpath, path.read_text(), result))
        print(json.dumps(result, indent=2))

    body = "\n---\n\n".join(sections)
    new_block = f"{START}\n\n{body}\n\n{END}"

    text = README.read_text()
    if START in text and END in text:
        text = re.sub(re.escape(START) + r".*?" + re.escape(END), new_block, text, flags=re.DOTALL)
    else:
        text += f"\n\n## Test Samples \u2014 Real Output\n\n{new_block}\n"
    README.write_text(text)
    print(f"\nWrote real review output for {len(SAMPLES)} samples into {README}")


if __name__ == "__main__":
    main()
