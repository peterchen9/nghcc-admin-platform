import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from modules.eureka.models import Member
from nads26.upload_validation import UploadValidationError, validate_uploaded_file


def make_upload(name, content=b"content", content_type="application/octet-stream"):
    return SimpleUploadedFile(name, content, content_type=content_type)


@override_settings(
    UPLOAD_ALLOWED_EXTENSIONS=["jpg", "jpeg", "png", "pdf"],
    UPLOAD_MAX_SIZE_MB=10,
    UPLOAD_STRICT_MIME_CHECK=False,
)
def test_upload_validation_rejects_exe():
    with pytest.raises(UploadValidationError):
        validate_uploaded_file(make_upload("virus.exe"))


@override_settings(
    UPLOAD_ALLOWED_EXTENSIONS=["jpg", "jpeg", "png", "pdf"],
    UPLOAD_MAX_SIZE_MB=1,
    UPLOAD_STRICT_MIME_CHECK=False,
)
def test_upload_validation_rejects_oversized_file():
    oversized = make_upload("large.pdf", b"x" * (1024 * 1024 + 1), "application/pdf")

    with pytest.raises(UploadValidationError):
        validate_uploaded_file(oversized)


@override_settings(
    UPLOAD_ALLOWED_EXTENSIONS=["jpg", "jpeg", "png", "pdf"],
    UPLOAD_MAX_SIZE_MB=10,
    UPLOAD_STRICT_MIME_CHECK=False,
)
@pytest.mark.parametrize(
    ("filename", "content_type"),
    [
        ("photo.jpg", "image/jpeg"),
        ("photo.png", "image/png"),
        ("document.pdf", "application/pdf"),
    ],
)
def test_upload_validation_allows_common_safe_extensions(filename, content_type):
    result = validate_uploaded_file(make_upload(filename, content_type=content_type))

    assert result.extension in {"jpg", "png", "pdf"}


@override_settings(
    UPLOAD_ALLOWED_EXTENSIONS=["jpg"],
    UPLOAD_MAX_SIZE_MB=10,
    UPLOAD_STRICT_MIME_CHECK=False,
)
def test_upload_validation_cleans_filename():
    result = validate_uploaded_file(make_upload('../bad name:photo.jpg', content_type="image/jpeg"))

    assert result.safe_name == "bad_name_photo.jpg"
    assert "/" not in result.safe_name
    assert "\\" not in result.safe_name


@override_settings(
    UPLOAD_ALLOWED_EXTENSIONS=["jpg"],
    UPLOAD_MAX_SIZE_MB=10,
    UPLOAD_STRICT_MIME_CHECK=True,
)
def test_upload_validation_can_reject_mime_mismatch_when_strict():
    with pytest.raises(UploadValidationError):
        validate_uploaded_file(make_upload("photo.jpg", b"not really an image", "application/pdf"))


def test_eureka_photo_upload_rejects_exe_before_creating_member(logged_in_client):
    before_count = Member.objects.count()
    response = logged_in_client.post(
        "/eureka/add/",
        {
            "name": "安全測試不應建立",
            "photo": make_upload("bad.exe", b"bad", "application/octet-stream"),
        },
    )

    assert response.status_code == 302
    assert Member.objects.count() == before_count
