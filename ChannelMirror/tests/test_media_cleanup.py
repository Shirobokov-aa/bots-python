from __future__ import annotations

from pathlib import Path

from app.services.media_cleanup import media_paths_from_payload, prune_orphan_media


def test_media_paths_from_payload() -> None:
    assert media_paths_from_payload({"type": "text"}) == []
    assert media_paths_from_payload({"type": "photo", "path": "data/media/a.jpg"}) == [
        "data/media/a.jpg"
    ]
    paths = media_paths_from_payload(
        {
            "type": "album",
            "items": [{"path": "data/media/1.jpg"}, {"path": "data/media/2.mp4"}],
        }
    )
    assert paths == ["data/media/1.jpg", "data/media/2.mp4"]


def test_prune_orphan_media(tmp_path: Path, monkeypatch) -> None:
    from app import config as config_mod

    media = tmp_path / "media"
    media.mkdir()
    keep = media / "keep.bin"
    drop = media / "drop.bin"
    keep.write_bytes(b"keep")
    drop.write_bytes(b"drop")

    monkeypatch.setenv("ADMIN_TELEGRAM_IDS", "1")
    monkeypatch.setenv("MEDIA_DIR", str(media))
    config_mod.get_settings.cache_clear()

    pending = [
        '{"type":"photo","path":"%s"}' % keep.resolve(),
    ]
    deleted = prune_orphan_media(pending)
    assert deleted == 1
    assert keep.exists()
    assert not drop.exists()
    config_mod.get_settings.cache_clear()
