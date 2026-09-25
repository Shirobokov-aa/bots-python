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


def test_invite_rejected_as_public() -> None:
    assert parse_channel("https://t.me/+AbCdEf") is None
    assert parse_channel("https://t.me/share/url") is None


def test_parse_invite() -> None:
    from app.services.parse_source import parse_invite

    inv = parse_invite("https://t.me/+AbCdEfGh")
    assert inv is not None
    assert inv.hash == "AbCdEfGh"

    inv = parse_invite("https://t.me/joinchat/AAAAA")
    assert inv is not None
    assert inv.hash == "AAAAA"

    assert parse_invite("@durov") is None


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


def test_source_footer_plain_text() -> None:
    from app.services.source_label import (
        append_source_footer,
        apply_source_label_to_payload,
        format_source_footer,
        source_display_name,
    )

    assert format_source_footer("Рога и копыта") == 'Источник: "Рога и копыта"'
    assert append_source_footer("Привет", "Рога и копыта") == (
        'Привет\n\nИсточник: "Рога и копыта"'
    )
    assert append_source_footer("", "X") == 'Источник: "X"'

    class _Src:
        title = "Рога и копыта"
        username = "roga"

    assert source_display_name(_Src()) == "Рога и копыта"

    class _OnlyUname:
        title = None
        username = "roga_kopyta"

    # no @ — must not become a Telegram mention/link
    assert source_display_name(_OnlyUname()) == "roga_kopyta"
    assert "@" not in format_source_footer(source_display_name(_OnlyUname()))

    payload = apply_source_label_to_payload({"type": "text", "text": "hi"}, "Канал")
    assert payload["text"].endswith('Источник: "Канал"')

    sticker = apply_source_label_to_payload({"type": "sticker", "path": "a.webp"}, "Канал")
    assert sticker.get("_source_followup") == 'Источник: "Канал"'
