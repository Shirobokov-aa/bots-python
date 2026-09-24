from app.services.parse_source import parse_channel


def test_at_and_links() -> None:
    p = parse_channel("добавь @durov")
    assert p is not None
    assert p.username == "durov"
    assert p.display == "@durov"

    p = parse_channel("https://t.me/s/varlamov_news")
    assert p is not None
    assert p.username == "varlamov_news"

    p = parse_channel("t.me/navalny")
    assert p is not None
    assert p.username == "navalny"


def test_invite_rejected() -> None:
    assert parse_channel("https://t.me/+AbCdEf") is None
    assert parse_channel("https://t.me/share/url") is None


def test_merge_album() -> None:
    from app.services.serialize import merge_album

    album = merge_album(
        [
            {"message_id": 2, "path": "b.jpg", "media_type": "photo", "text": ""},
            {"message_id": 1, "path": "a.jpg", "media_type": "photo", "text": "hi"},
        ]
    )
    assert album["type"] == "album"
    assert album["text"] == "hi"
    assert album["items"][0]["path"] == "a.jpg"
