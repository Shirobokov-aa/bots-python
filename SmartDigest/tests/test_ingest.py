from app.ingest.rss import parse_feed
from app.ingest.telegram import parse_telegram_html
from app.ingest.website import discover_feed_urls, looks_like_feed

RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Demo Feed</title>
    <item>
      <title>Первая новость</title>
      <link>https://example.com/one</link>
      <guid>one</guid>
      <description>&lt;p&gt;Короткий текст&lt;/p&gt;</description>
      <pubDate>Fri, 11 Sep 2026 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title></title>
      <link>https://example.com/empty</link>
    </item>
  </channel>
</rss>
""".encode()

TG_HTML = """
<html>
  <div class="tgme_channel_info_header_title">Durov</div>
  <div class="tgme_widget_message" data-post="durov/1">
    <div class="tgme_widget_message_text">Привет, мир</div>
    <a class="tgme_widget_message_date" href="https://t.me/durov/1">
      <time datetime="2026-09-11T10:00:00+00:00"></time>
    </a>
  </div>
  <div class="tgme_widget_message" data-post="durov/2">
    <a class="tgme_widget_message_date" href="https://t.me/durov/2"></a>
  </div>
</html>
"""

SITE_HTML = """
<html>
  <head>
    <link rel="alternate" type="application/rss+xml" href="/rss.xml">
  </head>
</html>
"""


def test_parse_rss() -> None:
    result = parse_feed(RSS, "https://example.com/rss")
    assert result.error is None
    assert result.title == "Demo Feed"
    assert len(result.items) == 1
    assert result.items[0].title == "Первая новость"
    assert result.items[0].url == "https://example.com/one"
    assert result.items[0].published_at is not None


def test_parse_telegram() -> None:
    result = parse_telegram_html(TG_HTML, "https://t.me/s/durov")
    assert result.title == "Durov"
    assert len(result.items) == 1
    assert result.items[0].url == "https://t.me/durov/1"
    assert result.items[0].title == "Привет, мир"


def test_discover_and_feed_sniff() -> None:
    urls = discover_feed_urls(SITE_HTML, "https://news.example/")
    assert "https://news.example/rss.xml" in urls
    assert looks_like_feed("application/rss+xml", RSS)
    assert not looks_like_feed("text/html", b"<html><rss")
