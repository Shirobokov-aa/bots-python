from datetime import datetime, timezone
from types import SimpleNamespace

from app.services.digest import build_digest, format_digest
from app.utils.text import content_hash


def _item(**kwargs):
    now = datetime(2026, 9, 11, 12, tzinfo=timezone.utc)
    title = kwargs.get("title", "Заголовок")
    url = kwargs.get("url", "https://example.com/1")
    defaults = dict(
        source_id=1,
        title=title,
        url=url,
        summary="Короткий текст",
        published_at=now,
        fetched_at=now,
        is_noise=False,
        content_hash=content_hash(title, url),
        source=SimpleNamespace(title="Habr"),
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_dedup_and_noise() -> None:
    items = [
        _item(title="Одна новость", url="https://a.test/1"),
        _item(title="Одна новость!!!", url="https://b.test/2", source_id=2, source=SimpleNamespace(title="VC")),
        _item(title="Реклама", url="https://c.test/ad", is_noise=True, content_hash="x"),
        _item(title="Другая", url="https://a.test/3", published_at=datetime(2026, 9, 11, 13, tzinfo=timezone.utc)),
    ]
    digest = build_digest(items, max_items=10, window_hours=24)
    titles = [entry.title for entry in digest.entries]
    assert titles[0] == "Другая"
    assert "Одна новость" in titles
    assert digest.skipped_dupes == 1
    assert digest.skipped_noise == 1
    assert digest.sources_count == 1


def test_truncates() -> None:
    items = [_item(title=f"n{i}", url=f"https://a.test/{i}", content_hash=str(i)) for i in range(5)]
    digest = build_digest(items, max_items=2, window_hours=24)
    assert len(digest.entries) == 2
    assert digest.truncated == 3


def test_format_empty() -> None:
    text = format_digest(build_digest([], max_items=5, window_hours=24))
    assert "ничего нового" in text
    assert "SmartDigest" in text
