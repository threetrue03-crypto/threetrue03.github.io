"""Validate post metadata without changing author-controlled headings or filenames."""

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "_posts"
REQUIRED = ("title", "description", "category")
LINK_FIELDS = ("source_url", "paper_url", "book_url")


def parse_front_matter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("front matter가 없습니다")
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as exc:
        raise ValueError("front matter 종료 구분자(---)가 없습니다") from exc

    data: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"\'')
    return data


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        data = parse_front_matter(path)
    except (OSError, UnicodeError, ValueError) as exc:
        return [str(exc)]

    for field in REQUIRED:
        if not data.get(field):
            errors.append(f"필수 항목 `{field}`가 비어 있습니다")

    inferred_date = re.search(r"\d{4}-\d{2}-\d{2}", path.name)
    if data.get("date"):
        try:
            dt.date.fromisoformat(data["date"][:10])
        except ValueError:
            errors.append("`date`는 YYYY-MM-DD 형식이어야 합니다")
    elif not inferred_date:
        errors.append("front matter 또는 파일명에 YYYY-MM-DD 날짜가 필요합니다")

    for field in LINK_FIELDS:
        value = data.get(field)
        if value and not re.match(r"^https?://", value, re.IGNORECASE):
            errors.append(f"`{field}`는 http:// 또는 https:// 주소여야 합니다")

    return errors


def main() -> int:
    failures: list[tuple[Path, list[str]]] = []
    posts = sorted(POSTS.rglob("*.md"))
    for path in posts:
        errors = validate(path)
        if errors:
            failures.append((path, errors))

    if failures:
        print(f"콘텐츠 검사 실패: {len(failures)}개 파일")
        for path, errors in failures:
            print(f"\n- {path.relative_to(ROOT)}")
            for error in errors:
                print(f"  · {error}")
        return 1

    print(f"콘텐츠 검사 완료: {len(posts)}개 글")
    print("참고: 본문 H1과 파일명/slug는 작성자의 의도에 따라 검사하지 않습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
