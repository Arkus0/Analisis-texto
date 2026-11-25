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


# --------------------------------------------------------------------------- zona de captura
from app.capture import crop_rect, prepare_image  # noqa: E402


def test_crop_rect_full_and_partial():
    assert crop_rect(1920, 1080, None) == (0, 0, 1920, 1080)
    assert crop_rect(1920, 1080, [0.25, 0.1, 0.5, 0.5]) == (480, 108, 960, 540)


def test_crop_rect_is_clamped_inside_image():
    x, y, w, h = crop_rect(1000, 500, [0.9, 0.9, 0.5, 0.5])
    assert (x, y) == (900, 450) and x + w <= 1000 and y + h <= 500 and w >= 1 and h >= 1


def test_prepare_image_crops_then_scales(qapp):
    img = QImage(3840, 2160, QImage.Format.Format_ARGB32)
    img.fill(QColor("#000000"))
    out = QImage.fromData(prepare_image(img, [0.25, 0.25, 0.5, 0.5], max_width=1280))
    assert (out.width(), out.height()) == (1280, 720)
    out = QImage.fromData(prepare_image(img, None, max_width=0))
    assert (out.width(), out.height()) == (3840, 2160)


def test_prepare_image_works_in_a_worker_thread(qapp):
    import threading

    img = QImage(1920, 1080, QImage.Format.Format_ARGB32)
    img.fill(QColor("#123456"))
    result = {}
    t = threading.Thread(target=lambda: result.setdefault("jpeg", prepare_image(img, [0, 0, 0.5, 0.5], 0)))
    t.start()
    t.join(10)
    assert result["jpeg"][:3] == b"\xff\xd8\xff"


def test_region_picker_rect_to_region(qapp):
    from PySide6.QtCore import QRect

    from app.region_picker import rect_to_region

    assert rect_to_region(QRect(480, 108, 960, 540), 1920, 1080) == [0.25, 0.1, 0.5, 0.5]
    assert rect_to_region(QRect(0, 0, 1920, 1080), 1920, 1080) is None  # = pantalla completa
    assert rect_to_region(QRect(10, 10, 5, 5), 1920, 1080) is None  # demasiado pequeña


def test_region_picker_drag_and_enter(qapp):
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QKeyEvent, QMouseEvent
    from PySide6.QtCore import QEvent

    from app.region_picker import RegionPicker

    picker = RegionPicker(qapp.primaryScreen())
    picker.show()
    got = []
    picker.picked.connect(got.append)
    w, h = picker.width(), picker.height()

    def mouse(kind, x, y):
        pos = QPointF(x, y)
        return QMouseEvent(kind, pos, pos, Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton,
                           Qt.KeyboardModifier.NoModifier)

    picker.mousePressEvent(mouse(QEvent.Type.MouseButtonPress, w * 0.25, h * 0.25))
    picker.mouseMoveEvent(mouse(QEvent.Type.MouseMove, w * 0.75, h * 0.75))
    picker.mouseReleaseEvent(mouse(QEvent.Type.MouseButtonRelease, w * 0.75, h * 0.75))
    assert not picker.grab().isNull()
    picker.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier))
    assert got and got[0] == pytest.approx([0.25, 0.25, 0.5, 0.5], abs=0.005)


def test_region_picker_escape_cancels(qapp):
    from PySide6.QtCore import QEvent, Qt
    from PySide6.QtGui import QKeyEvent

    from app.region_picker import RegionPicker

    picker = RegionPicker(qapp.primaryScreen(), [0.1, 0.1, 0.5, 0.5])
    got = []
    picker.picked.connect(got.append)
    picker.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier))
    assert got == ["cancel"]
