#!/usr/bin/env python3
"""Run lightweight integrity checks against the generated static site."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


class Document(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.references: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"] or "")
        for attribute in ("href", "src"):
            if values.get(attribute):
                self.references.append((attribute, values[attribute] or ""))


def read_document(path: Path) -> Document:
    document = Document()
    document.feed(path.read_text(encoding="utf-8"))
    return document


def main() -> None:
    pages = sorted(DIST.rglob("*.html"))
    if not pages:
        raise SystemExit("No generated HTML files found. Run scripts/build.py first.")

    parsed = {page.relative_to(DIST).as_posix(): read_document(page) for page in pages}
    errors: list[str] = []

    for page, document in parsed.items():
        page_path = DIST / page
        duplicates = sorted({item for item in document.ids if document.ids.count(item) > 1})
        if duplicates:
            errors.append(f"{page}: duplicate ids: {', '.join(duplicates)}")

        for attribute, raw_reference in document.references:
            reference = unquote(raw_reference)
            parts = urlsplit(reference)
            if parts.scheme in {"http", "https", "mailto", "tel", "data"} or reference.startswith("//"):
                continue

            target_page = page
            if parts.path:
                local_target = ((DIST if parts.path.startswith("/") else page_path.parent) / parts.path.lstrip("/")).resolve()
                try:
                    local_target.relative_to(DIST.resolve())
                except ValueError:
                    errors.append(f"{page}: {attribute} escapes dist: {reference}")
                    continue
                if not local_target.exists():
                    errors.append(f"{page}: missing local target: {reference}")
                    continue
                if local_target.suffix == ".html":
                    target_page = local_target.relative_to(DIST).as_posix()

            if parts.fragment:
                target_document = parsed.get(target_page)
                if target_document and parts.fragment not in target_document.ids:
                    errors.append(f"{page}: missing anchor #{parts.fragment} in {target_page}")

    if errors:
        raise SystemExit("Site checks failed:\n- " + "\n- ".join(errors))
    print(f"Checked {len(pages)} HTML pages: local references and anchors are valid.")


if __name__ == "__main__":
    main()
