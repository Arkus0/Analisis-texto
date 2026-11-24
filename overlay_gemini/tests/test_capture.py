import pytest
from PySide6.QtGui import QColor, QImage

from app.capture import CaptureError, encode_image, find_screen


def _img(w, h):
    img = QImage(w, h, QImage.Format.Format_ARGB32)
    img.fill(QColor("#224466"))
    return img


def test_encode_jpeg_and_downscale(qapp):
    data = encode_image(_img(3840, 2160), max_width=1920)
    assert data[:3] == b"\xff\xd8\xff"  # cabecera JPEG
    decoded = QImage.fromData(data)
    assert decoded.width() == 1920 and decoded.height() == 1080


def test_encode_keeps_size_when_smaller_or_unlimited(qapp):
    assert QImage.fromData(encode_image(_img(800, 600), max_width=1920)).width() == 800
    assert QImage.fromData(encode_image(_img(2560, 1440), max_width=0)).width() == 2560


def test_null_image_raises(qapp):
    with pytest.raises(CaptureError):
        encode_image(QImage())


def test_find_screen_falls_back_to_primary(qapp):
    assert find_screen("no-existe") == qapp.primaryScreen()
