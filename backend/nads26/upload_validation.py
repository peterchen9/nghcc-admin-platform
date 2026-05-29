import os
import re
from dataclasses import dataclass

from django.conf import settings


class UploadValidationError(ValueError):
    """上傳檔案驗證失敗。"""


@dataclass(frozen=True)
class ValidatedUpload:
    original_name: str
    safe_name: str
    extension: str


def _clean_filename(filename):
    basename = os.path.basename(filename or '').strip()
    basename = basename.replace('\x00', '')
    basename = re.sub(r'[\\/:*?"<>|]+', '_', basename)
    basename = re.sub(r'\s+', '_', basename)
    basename = basename.strip('._')
    if not basename:
        return 'upload'
    return basename[:180]


def _normalize_extensions(extensions):
    return {
        item.lower().lstrip('.').strip()
        for item in extensions
        if item and item.strip()
    }


def validate_uploaded_file(uploaded_file, allowed_extensions=None, max_size_mb=None):
    """驗證上傳檔案大小與副檔名，並回傳安全檔名。

    MIME type 第一階段先不硬性阻擋，因為瀏覽器與用戶端提供的 content_type
    容易被偽造；後續應改由檔案內容 sniffing 或專用函式庫判斷。
    """
    if not uploaded_file:
        raise UploadValidationError('未提供檔案。')

    safe_name = _clean_filename(uploaded_file.name)
    extension = os.path.splitext(safe_name)[1].lower().lstrip('.')
    if not extension:
        raise UploadValidationError('上傳檔案缺少副檔名。')

    if allowed_extensions is None:
        allowed_extensions = settings.UPLOAD_ALLOWED_EXTENSIONS
    allowed = _normalize_extensions(allowed_extensions)
    if extension not in allowed:
        allowed_text = '、'.join(sorted(allowed))
        raise UploadValidationError(f'不支援的檔案類型：.{extension}，僅接受：{allowed_text}。')

    limit_mb = max_size_mb if max_size_mb is not None else settings.UPLOAD_MAX_SIZE_MB
    max_size = int(limit_mb) * 1024 * 1024
    if uploaded_file.size > max_size:
        raise UploadValidationError(f'檔案大小超過限制：最大 {limit_mb} MB。')

    return ValidatedUpload(
        original_name=uploaded_file.name,
        safe_name=safe_name,
        extension=extension,
    )
