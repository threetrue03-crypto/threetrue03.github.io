"""Refresh the homepage briefing with recent HN stories and arXiv papers."""

from __future__ import annotations

import concurrent.futures
import datetime as dt
import html
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "_data" / "briefing.yml"
KST = dt.timezone(dt.timedelta(hours=9))
NOW = dt.datetime.now(KST)
USER_AGENT = "sejin.dev-briefing/1.0 (GitHub Pages briefing updater)"

TOPICS = {
    "Physical AI": (
        "physical ai", "physical intelligence", "embodied ai", "embodied agent",
        "vision language action", "vision-language-action", "vla model", "robot learning",
        "robotics foundation", "world model", "humanoid robot",
    ),
    "Architecture": (
        "computer architecture", "risc-v", "risc v", "gpu", "npu", "tpu", "chiplet",
        "ai accelerator", "hardware accelerator", "memory hierarchy", "hbm", "neuromorphic",
    ),
    "Computer Vision": (
        "computer vision", "vision model", "image segmentation", "object detection",
        "video understanding", "3d vision", "visual recognition", "multimodal vision",
    ),
    "Machine Learning": (
        "machine learning", "deep learning", "neural network", "transformer", "diffusion model",
        "representation learning", "reinforcement learning", "foundation model",
    ),
}


def request_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read()


def request_json(url: str):
    return json.loads(request_bytes(url))


def normalize(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


def classify(text: str) -> tuple[str, int]:
    lowered = text.lower()
    scored = []
    for topic, keywords in TOPICS.items():
        score = sum(
            3
            for keyword in keywords
            if re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", lowered)
        )
        scored.append((score, topic))
    score, topic = max(scored)
    return topic, score


def diversify(items: list[dict], limit: int = 12) -> list[dict]:
    selected: list[dict] = []
    used_topics: set[str] = set()
    for item in items:
        if item["topic"] not in used_topics:
            selected.append(item)
            used_topics.add(item["topic"])
        if len(selected) == limit:
            return selected
    for item in items:
        if item not in selected:
            selected.append(item)
        if len(selected) == limit:
            break
    return selected


def fetch_hn_item(item_id: int) -> dict | None:
    try:
        item = request_json(f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json")
    except Exception:
        return None
    if not item or item.get("type") != "story" or not item.get("url") or not item.get("title"):
        return None
    published = dt.datetime.fromtimestamp(item.get("time", 0), tz=dt.timezone.utc).astimezone(KST)
    if published < NOW - dt.timedelta(days=7):
        return None
    topic, relevance = classify(item["title"])
    if relevance == 0:
        return None
    points = int(item.get("score", 0))
    comments = int(item.get("descendants", 0))
    return {
        "topic": topic,
        "published": published.strftime("%Y.%m.%d"),
        "title": normalize(item["title"]),
        "summary": f"Hacker News에서 {points}개의 추천과 {comments}개의 댓글을 받은 {topic} 관련 소식입니다.",
        "source": urllib.parse.urlparse(item["url"]).netloc.removeprefix("www."),
        "url": item["url"],
        "_rank": relevance * 1000 + points,
    }


def fetch_news() -> list[dict]:
    new_ids = request_json("https://hacker-news.firebaseio.com/v0/newstories.json")
    top_ids = request_json("https://hacker-news.firebaseio.com/v0/topstories.json")
    ids = list(dict.fromkeys(top_ids + new_ids))[:500]
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        items = [item for item in executor.map(fetch_hn_item, ids) if item]
    items.sort(key=lambda item: item["_rank"], reverse=True)
    selected = diversify(items)
    for item in selected:
        item.pop("_rank", None)
    return selected


def fetch_papers() -> list[dict]:
    query = " OR ".join(f"cat:{category}" for category in ("cs.RO", "cs.AR", "cs.CV", "cs.LG", "stat.ML"))
    params = urllib.parse.urlencode({
        "search_query": f"({query})",
        "start": 0,
        "max_results": 80,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    root = ET.fromstring(request_bytes(f"https://export.arxiv.org/api/query?{params}"))
    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    items = []
    for entry in root.findall("atom:entry", namespace):
        title = normalize(entry.findtext("atom:title", default="", namespaces=namespace))
        summary = normalize(entry.findtext("atom:summary", default="", namespaces=namespace))
        published_text = entry.findtext("atom:published", default="", namespaces=namespace)
        published = dt.datetime.fromisoformat(published_text.replace("Z", "+00:00")).astimezone(KST)
        if published < NOW - dt.timedelta(days=14):
            continue
        topic, relevance = classify(f"{title} {summary}")
        if relevance == 0:
            continue
        url = entry.findtext("atom:id", default="", namespaces=namespace)
        authors = ", ".join(
            normalize(author.findtext("atom:name", default="", namespaces=namespace))
            for author in entry.findall("atom:author", namespace)
        )
        pdf_url = ""
        for link in entry.findall("atom:link", namespace):
            if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
                pdf_url = link.attrib.get("href", "")
                break
        items.append({
            "topic": topic,
            "published": published.strftime("%Y.%m.%d"),
            "title": title,
            "summary": summary[:260].rstrip() + ("…" if len(summary) > 260 else ""),
            "source": "arXiv",
            "url": url,
            "authors": authors,
            "pdf_url": pdf_url,
            "_rank": relevance * 1000 + int(published.timestamp() / 86400),
        })
    items.sort(key=lambda item: item["_rank"], reverse=True)
    selected = diversify(items)
    for item in selected:
        item.pop("_rank", None)
    return selected


def load_current() -> dict:
    if not OUTPUT.exists():
        return {}
    return yaml.safe_load(OUTPUT.read_text(encoding="utf-8")) or {}


def merge_items(fresh: list[dict], stored: list[dict], retention_days: int, limit: int = 100) -> list[dict]:
    """Merge newest results into stored history, de-duplicate URLs, and trim old entries."""
    if not fresh:
        return stored[:limit]

    cutoff = (NOW - dt.timedelta(days=retention_days)).date()
    merged = []
    seen_urls = set()
    for item in fresh + stored:
        url = item.get("url", "")
        if not url or url in seen_urls or item.get("published") == "Preview":
            continue
        try:
            published = dt.datetime.strptime(item.get("published", ""), "%Y.%m.%d").date()
        except ValueError:
            continue
        if published < cutoff:
            continue
        seen_urls.add(url)
        merged.append(item)

    merged.sort(key=lambda item: item.get("published", ""), reverse=True)
    return merged[:limit]


def main() -> None:
    current = load_current()
    errors = []
    try:
        news = fetch_news()
    except Exception as exc:
        errors.append(f"news: {exc}")
        news = []
    try:
        papers = fetch_papers()
    except Exception as exc:
        errors.append(f"papers: {exc}")
        papers = []

    data = {
        "updated_at": NOW.strftime("%Y.%m.%d %H:%M KST 갱신"),
        "news": merge_items(news, current.get("news", []), retention_days=30),
        "papers": merge_items(papers, current.get("papers", []), retention_days=90),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000), encoding="utf-8")
    print(f"Updated {len(data['news'])} news items and {len(data['papers'])} papers.")
    if errors:
        print("Warnings: " + " | ".join(errors))


if __name__ == "__main__":
    main()
