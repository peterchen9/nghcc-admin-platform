from pathlib import Path

from django.conf import settings


def test_media_root_exists_and_is_readable():
    media_root = Path(settings.MEDIA_ROOT)

    assert media_root.exists()
    assert media_root.is_dir()
    assert any(media_root.iterdir())


def test_media_file_count_matches_restored_volume():
    media_root = Path(settings.MEDIA_ROOT)
    file_count = sum(1 for path in media_root.rglob("*") if path.is_file() and path.name != ".gitkeep")

    assert file_count >= 33827
