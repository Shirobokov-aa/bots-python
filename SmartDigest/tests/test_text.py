from app.utils.text import canonicalize_url, content_hash, looks_like_noise, normalize_title, snippet, split_telegram


def test_canonicalize_strips_utm() -> None:
    url = "https://Example.com/a/b/?utm_source=tg&id=1"
    assert canonicalize_url(url) == "https://example.com/a/b?id=1"


def test_same_title_same_hash() -> None:
    assert content_hash("Hello, World!", "https://x.test/a?utm_medium=1") == content_hash(
        "hello world", "https://x.test/a"
    )


def test_noise_markers() -> None:
    assert looks_like_noise("Обзор", "erid: 2W5z1 и промокод SUMMER")
    assert not looks_like_noise("Релиз Python 3.13", "Что нового в стандартной библиотеке")


def test_snippet_and_split() -> None:
    assert snippet("a" * 50) == "a" * 50
    assert snippet("слово " * 80).endswith("…")
    chunks = split_telegram("a" * 100, limit=40)
    assert len(chunks) > 1
    assert "".join(chunks).replace("\n", "") == "a" * 100 or all(len(c) <= 40 for c in chunks)


def test_normalize_title() -> None:
    assert normalize_title("<b>Новость!!!</b>") == "новость"
