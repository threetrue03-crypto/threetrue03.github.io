param(
  [Parameter(Mandatory=$true)][ValidateSet('notes','news','papers','books')][string]$Type,
  [Parameter(Mandatory=$true)][string]$Slug,
  [string]$Date = (Get-Date -Format 'yyyy-MM-dd')
)

$root = Split-Path -Parent $PSScriptRoot
$templateName = switch ($Type) {
  'notes' { 'note.md' }
  'news' { 'news.md' }
  'papers' { 'paper.md' }
  'books' { 'book.md' }
}
$template = Join-Path $root "_templates/$templateName"
$targetDir = Join-Path $root "_posts/$Type"
$target = Join-Path $targetDir "$Date-$Slug.md"

if (-not (Test-Path -LiteralPath $template)) { throw "템플릿을 찾을 수 없습니다: $template" }
if (Test-Path -LiteralPath $target) { throw "이미 같은 파일이 있습니다: $target" }

New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
$content = (Get-Content -Raw -Encoding utf8 -LiteralPath $template) -replace 'date: \d{4}-\d{2}-\d{2}', "date: $Date"
Set-Content -Encoding utf8 -LiteralPath $target -Value $content
Write-Host "새 기록을 만들었습니다: $target"
