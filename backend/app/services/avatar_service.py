import warnings
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.exceptions import BadRequestError

MAX_BYTES = 2 * 1024 * 1024


def normalize_avatar(data: bytes) -> bytes:
    if not data or len(data) > MAX_BYTES:
        raise BadRequestError("Ảnh phải có dung lượng từ 1 byte đến 2 MB")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    raise BadRequestError("Chọn ảnh JPG, PNG hoặc WebP")
                if image.width * image.height > 16_000_000:
                    raise BadRequestError("Ảnh quá lớn, tối đa 16 triệu điểm ảnh")
                image = ImageOps.exif_transpose(image)
                image = ImageOps.fit(image.convert("RGB"), (384, 384))
                output = BytesIO()
                image.save(output, "JPEG", quality=85)
                return output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise BadRequestError("Tệp không phải ảnh hợp lệ") from None
