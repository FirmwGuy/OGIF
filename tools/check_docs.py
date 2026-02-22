#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DocError:
    path: Path
    message: str


def _iter_markdown_files(repo_root: Path) -> list[Path]:
    return sorted(
        p
        for p in repo_root.rglob("*.md")
        if ".git" not in p.parts and p.is_file()
    )


def _check_utf8_and_newlines(path: Path, errors: list[DocError]) -> str | None:
    data = path.read_bytes()
    if b"\r" in data:
        errors.append(DocError(path, "Contains CR bytes (expected LF-only)."))
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        errors.append(DocError(path, f"Not valid UTF-8: {exc}"))
        return None


def _check_code_fences(path: Path, text: str, errors: list[DocError]) -> None:
    in_fence = False
    fence = "```"
    for i, line in enumerate(text.splitlines(), start=1):
        if line.strip() == "````":
            errors.append(DocError(path, f"Line {i}: Found four-backtick fence (````)."))

        if line.startswith(fence):
            in_fence = not in_fence

    if in_fence:
        errors.append(DocError(path, "Unclosed ``` code fence."))


def _check_doc_header(path: Path, text: str, errors: list[DocError]) -> None:
    # Lightweight sanity checks: specs should be self-describing.
    required = ["**Last Updated:**"]
    for token in required:
        if token not in text:
            errors.append(DocError(path, f"Missing required header token: {token}"))

    one_of = ["**Status:**", "**Document Type:**"]
    if not any(token in text for token in one_of):
        errors.append(
            DocError(
                path,
                "Missing header token: expected one of "
                + " / ".join(one_of)
                + ".",
            )
        )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    md_files = _iter_markdown_files(repo_root)
    errors: list[DocError] = []

    for path in md_files:
        text = _check_utf8_and_newlines(path, errors)
        if text is None:
            continue
        _check_code_fences(path, text, errors)
        _check_doc_header(path, text, errors)

    if errors:
        for err in errors:
            rel = err.path.relative_to(repo_root)
            print(f"{rel}: {err.message}")
        print(f"\nFAIL ({len(errors)} issue(s))")
        return 1

    print(f"OK ({len(md_files)} Markdown file(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
