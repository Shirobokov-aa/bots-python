from app.ingest.parse_source import parse_source
from app.bot.handlers import parse_hour


def test_telegram_at_and_links() -> None:
    parsed = parse_source("добавь @durov")
    assert parsed is not None
    assert parsed.kind == "telegram"
    assert parsed.username == "durov"
    assert parsed.url == "https://t.me/s/durov"

    parsed = parse_source("https://t.me/s/varlamov_news")
    assert parsed is not None
    assert parsed.kind == "telegram"
    assert parsed.username == "varlamov_news"

    parsed = parse_source("t.me/navalny")
    assert parsed is not None
    assert parsed.username == "navalny"


def test_invite_and_reserved_rejected() -> None:
    assert parse_source("https://t.me/+AbCdEf") is None
    assert parse_source("https://t.me/share/url") is None


def test_rss_and_website() -> None:
    rss = parse_source("https://habr.com/ru/rss/all/all/?fl=ru")
    assert rss is not None
    assert rss.kind == "rss"

    feed = parse_source("https://example.com/feed")
    assert feed is not None
    assert feed.kind == "rss"

    site = parse_source("смотри https://habr.com/ru/articles/")
    assert site is not None
    assert site.kind == "website"

    feedback = parse_source("https://example.com/feedback")
    assert feedback is not None
    assert feedback.kind == "website"


def test_parse_hour() -> None:
    assert parse_hour("9") == 9
    assert parse_hour("09:00") == 9
    assert parse_hour("21") == 21
    assert parse_hour("24") is None
    assert parse_hour("9:30") is None
    assert parse_hour("нет") is None
