# Markdown 작성 방법

- 기술 노트는 `note.md`를 복사해 `_posts/notes/YYYY-MM-DD-title.md`로 저장합니다.
- 뉴스는 `news.md`를 복사해 `_posts/news/YYYY-MM-DD-title.md`로 저장합니다.
- 논문은 `paper.md`를 복사해 `_posts/papers/YYYY-MM-DD-title.md`로 저장합니다.
- 책은 `book.md`를 복사해 `_posts/books/YYYY-MM-DD-title.md`로 저장합니다.
- `type: news`, `type: paper`, `type: book`은 페이지 분류에 사용되므로 변경하지 않습니다.
- `category`는 Topics 필터에 표시됩니다.
- `source_url`, `paper_url`, `book_url`을 적으면 글과 목록에 원문 링크가 표시됩니다.
- `status`, `rating`, `authors`, `venue`, `finished_at`, `last_modified_at`은 모두 선택 항목입니다. 적은 값만 목록과 본문에 표시됩니다.
- 공개 전 초안은 `_drafts` 폴더에 두거나 front matter에 `published: false`를 추가합니다.
- 본문 수식이 자동 감지되지 않는 경우 front matter에 `math: true`를 추가합니다.

## 새 글을 빠르게 만들기

PowerShell에서 다음처럼 실행하면 오늘 날짜로 템플릿 파일이 만들어집니다.

```powershell
./scripts/new-post.ps1 -Type notes -Slug conditional-expression
```

GitHub에 올릴 때마다 필수 항목 누락 여부를 자동 검사합니다. 의도적으로 사용 중인 본문 H1과 파일명은 검사하지 않습니다.
