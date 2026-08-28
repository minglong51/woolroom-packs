#!/usr/bin/env python3
"""Verify pack index rows with the published Woolpack release.

The index promises "review is of the link line, not your taste — woolpack lint
decides what's well-formed". This script makes that promise mechanical by
rendering and strict-linting every selected pack:

    python3 scripts/verify_rows.py                 # every row
    python3 scripts/verify_rows.py --base <ref>    # rows ADDED vs ref

`--base` mode (used by the PR workflow) verifies only rows added to HEAD's
README.md since `git show <ref>:README.md`, so documentation PRs pass
trivially. A row's first cell must be a markdown link to a public GitHub repo —
either a plain repo URL for a root-level pack or an immutable
`/tree/<full-commit-sha>/<subdir>` link naming the pack directory inside it.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

PACK_TABLE_HEADING = "## The list"
PACK_TABLE_HEADER = "| Pack | Figure | Species | Author | One-liner |"
TABLE_SEPARATOR_CELL = re.compile(r"^:?-{3,}:?$")
LINK_CELL = re.compile(r"^\[([^\]]+)\]\(([^)]+)\)$")
GITHUB_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
FULL_COMMIT = re.compile(r"^[0-9a-fA-F]{40}$")
COMMAND_TIMEOUT_SECONDS = 120
WOOLPACK = [
    "uvx",
    "--isolated",
    "--no-config",
    "--no-sources",
    "--from",
    "woolpack==0.1.1",
    "woolpack",
]


def table_rows(readme_text: str) -> list[str]:
    rows: list[str] = []
    state = "heading"
    for raw_line in readme_text.splitlines():
        line = raw_line.strip()
        if state == "heading":
            if line == PACK_TABLE_HEADING:
                state = "header"
            continue
        if state == "header":
            if not line:
                continue
            if line != PACK_TABLE_HEADER:
                raise ValueError("pack table must keep its five-column header")
            state = "separator"
            continue
        if state == "separator":
            cells = [cell.strip() for cell in line[1:-1].split("|")]
            if (
                not line.startswith("|")
                or not line.endswith("|")
                or len(cells) != 5
                or not all(TABLE_SEPARATOR_CELL.fullmatch(cell) for cell in cells)
            ):
                raise ValueError("pack table must keep its five-column separator")
            state = "rows"
            continue
        if not line or line.startswith("## "):
            break
        rows.append(line)
    if state == "heading":
        raise ValueError(f"README must contain the {PACK_TABLE_HEADING!r} section")
    if state in {"header", "separator"}:
        raise ValueError("README pack table is incomplete")
    return rows


def parse_row(row: str) -> tuple[str, str]:
    if not row.startswith("|") or not row.endswith("|"):
        raise ValueError("pack table row must start and end with '|'")
    cells = [cell.strip() for cell in row[1:-1].split("|")]
    if len(cells) != 5 or any(not cell for cell in cells):
        raise ValueError("pack table row must contain exactly five non-empty cells")
    link = LINK_CELL.fullmatch(cells[0])
    if link is None:
        raise ValueError("pack cell must be a complete Markdown link")
    return link.group(1), link.group(2)


def resolve(url: str) -> tuple[str, str | None, str]:
    """Return clone URL, commit or None, and repository-relative pack path."""
    parsed = urlsplit(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("repository URL has an invalid port") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname != "github.com"
        or parsed.username is not None
        or parsed.password is not None
        or port is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "repository link must be a credential-free HTTPS github.com URL"
        )

    parts = parsed.path.strip("/").split("/")
    if len(parts) < 2 or not all(GITHUB_COMPONENT.fullmatch(p) for p in parts[:2]):
        raise ValueError("repository link must name a GitHub owner and repository")
    owner, repository = parts[:2]
    clone_url = f"https://github.com/{owner}/{repository}"
    if len(parts) == 2:
        return clone_url, None, "."
    if len(parts) < 5 or parts[2] != "tree":
        raise ValueError(
            "repository link must be a repo root or "
            "/tree/<full-commit-sha>/<subdir> URL"
        )

    commit = parts[3]
    subdir_parts = parts[4:]
    if FULL_COMMIT.fullmatch(commit) is None:
        raise ValueError("tree link must use a full 40-character commit SHA")
    if any(
        not part
        or part in {".", ".."}
        or any(char.isspace() or char in "\\*?[%" for char in part)
        for part in subdir_parts
    ):
        raise ValueError("pack path contains an unsupported segment")
    if len(subdir_parts) > 32:
        raise ValueError("tree link has too many path segments")
    return clone_url, commit, str(PurePosixPath(*subdir_parts))


def run_command(command: list[str], label: str) -> int | None:
    try:
        return subprocess.run(
            command,
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
        ).returncode
    except subprocess.TimeoutExpired:
        print(f"::error::{label} timed out after {COMMAND_TIMEOUT_SECONDS} seconds")
        return None
    except OSError as exc:
        print(f"::error::{label} could not start: {exc}")
        return None


def clone_repository(
    clone_url: str,
    ref: str | None,
    destination: Path,
) -> bool:
    if ref is None:
        return (
            run_command(
                ["git", "clone", "--depth", "1", "--", clone_url, str(destination)],
                f"clone {clone_url}",
            )
            == 0
        )

    commands = [
        (["git", "init", "--quiet", str(destination)], "initialize repository"),
        (
            ["git", "-C", str(destination), "remote", "add", "origin", clone_url],
            "configure repository remote",
        ),
        (
            [
                "git",
                "-C",
                str(destination),
                "fetch",
                "--depth",
                "1",
                "--",
                "origin",
                ref,
            ],
            f"fetch {ref}",
        ),
        (
            [
                "git",
                "-C",
                str(destination),
                "checkout",
                "--quiet",
                "--detach",
                "FETCH_HEAD",
            ],
            f"check out {ref}",
        ),
    ]
    return all(run_command(command, label) == 0 for command, label in commands)


def verify_row(row: str) -> bool:
    try:
        name, url = parse_row(row)
        clone_url, ref, subdir = resolve(url)
    except ValueError as exc:
        print("::group::Invalid pack row")
        print(f"::error::{exc}: {row}")
        print("::endgroup::", flush=True)
        return False

    # flush before subprocess output shares the stream, or the group
    # markers arrive out of order in the Actions log
    print(f"::group::{name} — {url}", flush=True)
    ok = False
    with tempfile.TemporaryDirectory() as tmp:
        repo_root = Path(tmp) / "pack-repo"
        if not clone_repository(clone_url, ref, repo_root):
            print(f"::error::{name}: could not clone {clone_url}")
        else:
            resolved_root = repo_root.resolve()
            pack_dir = (repo_root / subdir).resolve()
            if not pack_dir.is_relative_to(resolved_root):
                print(f"::error::{name}: pack directory escapes the repository")
            elif not (pack_dir / "pack.yaml").is_file():
                print(f"::error::{name}: {subdir}/pack.yaml not found in {clone_url}")
            else:
                board = Path(tmp) / "pack-board.html"
                render_code = run_command(
                    [*WOOLPACK, "render", str(pack_dir), "-o", str(board)],
                    f"{name}: woolpack render",
                )
                render_ok = (
                    render_code == 0 and board.is_file() and board.stat().st_size > 0
                )
                if render_code not in {0, None}:
                    print(f"::error::{name}: woolpack render failed")
                elif not render_ok:
                    print(f"::error::{name}: woolpack render produced no review board")
                lint_code = run_command(
                    [*WOOLPACK, "lint", str(pack_dir), "--strict"],
                    f"{name}: woolpack lint --strict",
                )
                if lint_code not in {0, None}:
                    print(f"::error::{name}: woolpack lint --strict failed")
                ok = render_ok and lint_code == 0
    print("::endgroup::", flush=True)
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--base", default=None, help="git ref; verify only rows added since it"
    )
    args = parser.parse_args()

    try:
        head_rows = table_rows(Path("README.md").read_text(encoding="utf-8"))
    except ValueError as exc:
        print(f"::error::{exc}")
        return 1
    rows = head_rows
    if args.base:
        try:
            shown = subprocess.run(
                ["git", "show", f"{args.base}:README.md"],
                capture_output=True,
                check=False,
                text=True,
                timeout=COMMAND_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            print(f"::error::reading {args.base}:README.md timed out")
            return 1
        try:
            base_rows = (
                Counter(table_rows(shown.stdout))
                if shown.returncode == 0
                else Counter()
            )
        except ValueError as exc:
            print(f"::error::{args.base}:README.md is malformed: {exc}")
            return 1
        rows = []
        for row in head_rows:
            if base_rows[row]:
                base_rows[row] -= 1
            else:
                rows.append(row)

    if not rows:
        print("no added pack rows — nothing to verify")
        return 0

    results = [verify_row(row) for row in rows]
    failed = results.count(False)
    print(f"{len(results) - failed}/{len(results)} rows verified clean")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
