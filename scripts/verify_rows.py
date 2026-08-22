#!/usr/bin/env python3
"""Verify pack index rows: clone each linked pack and run woolroom's
pack_lint --strict against it.

The index promises "review is of the link line, not your taste — pack lint
decides what's well-formed". This script makes that promise mechanical:

    python3 scripts/verify_rows.py --woolroom <checkout>            # every row
    python3 scripts/verify_rows.py --woolroom <checkout> --base <ref>  # rows ADDED vs ref

`--base` mode (used by the PR workflow) verifies only rows present in HEAD's
README.md but not in `git show <ref>:README.md`, so documentation PRs pass
trivially. A row's first cell must be a markdown link to a public git repo —
either a plain clone URL or a GitHub `/tree/<ref>/<subdir>` link naming the
pack directory inside it.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROW_LINK = re.compile(r"^\|\s*\[([^\]]+)\]\(([^)]+)\)")
GITHUB_TREE = re.compile(
    r"^(https://github\.com/[^/]+/[^/]+)/tree/([^/]+)/(.+?)/?$"
)


def table_rows(readme_text: str) -> list[str]:
    rows = []
    for line in readme_text.splitlines():
        if ROW_LINK.match(line):
            rows.append(line.strip())
    return rows


def parse_row(row: str) -> tuple[str, str]:
    m = ROW_LINK.match(row)
    assert m is not None
    return m.group(1), m.group(2)


def resolve(url: str) -> tuple[str, str | None, str]:
    """(clone_url, ref or None, subdir) for a row link."""
    m = GITHUB_TREE.match(url)
    if m:
        return m.group(1), m.group(2), m.group(3)
    return url.rstrip("/"), None, "."


def verify_row(row: str, woolroom: Path) -> bool:
    name, url = parse_row(row)
    clone_url, ref, subdir = resolve(url)
    # flush before subprocess output shares the stream, or the group
    # markers arrive out of order in the Actions log
    print(f"::group::{name} — {url}", flush=True)
    ok = False
    with tempfile.TemporaryDirectory() as tmp:
        clone = ["git", "clone", "--depth", "1"]
        if ref:
            clone += ["--branch", ref]
        clone += [clone_url, tmp + "/pack-repo"]
        if subprocess.run(clone).returncode != 0:
            print(f"::error::{name}: could not clone {clone_url}")
        else:
            pack_dir = Path(tmp) / "pack-repo" / subdir
            if not (pack_dir / "pack.yaml").is_file():
                print(f"::error::{name}: {subdir}/pack.yaml not found in {clone_url}")
            else:
                lint = subprocess.run(
                    [
                        sys.executable,
                        str(woolroom / "scripts" / "pack_lint.py"),
                        str(pack_dir),
                        "--strict",
                    ],
                    cwd=woolroom,
                )
                ok = lint.returncode == 0
                if not ok:
                    print(f"::error::{name}: pack_lint --strict failed")
    print("::endgroup::", flush=True)
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--woolroom", required=True, help="path to a woolroom checkout")
    parser.add_argument("--base", default=None, help="git ref; verify only rows added since it")
    args = parser.parse_args()

    head_rows = table_rows(Path("README.md").read_text(encoding="utf-8"))
    rows = head_rows
    if args.base:
        shown = subprocess.run(
            ["git", "show", f"{args.base}:README.md"],
            capture_output=True,
            text=True,
        )
        base_rows = set(table_rows(shown.stdout)) if shown.returncode == 0 else set()
        rows = [r for r in head_rows if r not in base_rows]

    if not rows:
        print("no added pack rows — nothing to verify")
        return 0

    results = [verify_row(row, Path(args.woolroom).resolve()) for row in rows]
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} rows verified clean")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
