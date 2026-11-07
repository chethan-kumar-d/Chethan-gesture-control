"""Camera-free regression checks. All mouse actions use an injected fake module."""
import importlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
fake_mouse = SimpleNamespace(size=lambda: (1920, 1080), FAILSAFE=True,
    move=Mock(), click=Mock(), rightClick=Mock(), mouseDown=Mock(),
    mouseUp=Mock(), scroll=Mock())
sys.modules['pyautogui'] = fake_mouse
import cv2
# Any accidental camera access is a hard failure, even during imports.
cv2.VideoCapture = Mock(side_effect=AssertionError('Camera access forbidden'))
from gesture_v3.core.system import SystemController
from gesture_v3.intent.classifier import GestureClassifier
from gesture_v3.control.mouse_physics import PhysicsCursor
from gesture_v3 import config


def hand(kind='palm', x=0.5, y=0.5):
    pts = [SimpleNamespace(x=x, y=y + 0.1) for _ in range(21)]
    pts[0] = SimpleNamespace(x=x, y=y + 0.2)
    pts[5] = SimpleNamespace(x=x, y=y)
    pts[4] = SimpleNamespace(x=x - 0.18, y=y - 0.05)
    for i, offset in zip((8, 12, 16, 20), (-0.04, 0.04, 0.10, 0.16)):
        pts[i - 2] = SimpleNamespace(x=x + offset, y=y)
        pts[i] = SimpleNamespace(x=x + offset, y=y - 0.15)
    if kind == 'fist':
        for i in (8, 12, 16, 20):
            pts[i].y = y + 0.1
        # A fist can put thumb and index together; it must still grab.
        pts[4] = SimpleNamespace(x=pts[8].x, y=pts[8].y)
    if kind == 'scroll':
        pts[16].y = pts[20].y = y + 0.1
    if kind in ('left', 'right', 'hysteresis'):
        target = pts[12] if kind == 'right' else pts[8]
        pts[4] = SimpleNamespace(x=target.x + (0.075 if kind == 'hysteresis' else 0.01), y=target.y)
    return pts


class ControlsTest(unittest.TestCase):
    def setUp(self):
        for name in ('move', 'click', 'rightClick', 'mouseDown', 'mouseUp', 'scroll'):
            getattr(fake_mouse, name).reset_mock()
        self.app = SystemController.__new__(SystemController)
        self.app._init_controls()
        self.now = 10.0
        self.clock = patch('gesture_v3.intent.classifier.time.monotonic', side_effect=lambda: self.now)
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def frame(self, kind='palm', x=0.5, y=0.5):
        self.now += 1 / 60
        return self.app._process_hand(None if kind is None else hand(kind, x, y), self.now, 1 / 60)

    def hold(self, kind, count=120):
        return [self.frame(kind)[0] for _ in range(count)]

    def test_one_click_per_pinch_and_separation(self):
        states = self.hold('left')
        self.assertEqual(states[0], 'CLICK_PENDING')
        fake_mouse.click.assert_called_once()
        self.assertEqual(states.count('CLICK_LEFT'), 1)
        self.hold('hysteresis', 20)
        self.hold('left', 20)
        self.hold('right', 20)  # Switching pinch type is not separation.
        fake_mouse.click.assert_called_once()
        fake_mouse.rightClick.assert_not_called()
        self.hold('palm', 30)
        self.hold('right', 120)
        fake_mouse.rightClick.assert_called_once()

    def test_second_pinch_waits_for_cooldown_without_losing_click(self):
        self.hold('left', 6)
        fake_mouse.click.assert_called_once()
        self.frame('palm')
        self.hold('left', 6)
        fake_mouse.click.assert_called_once()
        self.hold('left', 60)
        self.assertEqual(fake_mouse.click.call_count, 2)

    def test_unstable_pinch_does_not_confirm(self):
        self.frame('palm')
        for i in range(20):
            self.frame('left', x=0.3 if i % 2 else 0.7)
        fake_mouse.click.assert_not_called()

    def test_freeze_and_rebase_after_pinch(self):
        self.frame('palm', x=0.2)
        self.frame('palm', x=0.3)
        fake_mouse.move.reset_mock()
        for i in range(20):
            self.frame('left', x=0.3 + i * 0.01)
        fake_mouse.move.assert_not_called()
        self.frame('palm', x=0.8)
        self.frame('palm', x=0.8)
        fake_mouse.move.assert_not_called()
        self.frame('palm', x=0.82)
        self.assertTrue(fake_mouse.move.called)

    def test_fist_grabs_once_palm_drops_once(self):
        self.frame('palm', x=0.2)
        self.frame('fist', x=0.8)
        fake_mouse.move.assert_not_called()
        self.hold('fist', 180)
        fake_mouse.mouseDown.assert_called_once()
        fake_mouse.mouseUp.assert_not_called()
        self.assertTrue(self.app.drag_active)
        self.frame('fist', x=0.55)
        self.assertTrue(fake_mouse.move.called)
        fake_mouse.move.reset_mock()
        self.frame('palm', x=0.9)
        self.frame('palm', x=0.9)
        self.frame('palm', x=0.9)
        fake_mouse.move.assert_not_called()
        fake_mouse.mouseUp.assert_called_once()
        self.assertFalse(self.app.drag_active)
        self.frame('fist')
        self.assertEqual(fake_mouse.mouseDown.call_count, 2)

    def test_drag_blocks_click_scroll_and_rebases(self):
        self.frame('fist')
        self.frame('fist', x=0.55)
        fake_mouse.move.reset_mock()
        self.hold('left')
        self.hold('right')
        for y in (0.3, 0.4, 0.5):
            self.frame('scroll', y=y)
        fake_mouse.click.assert_not_called()
        fake_mouse.rightClick.assert_not_called()
        fake_mouse.scroll.assert_not_called()
        fake_mouse.move.assert_not_called()
        self.frame('fist', x=0.9)
        fake_mouse.move.assert_not_called()
        self.frame('palm')
        fake_mouse.click.assert_not_called()

    def test_hand_loss_releases_and_clears_all_references(self):
        self.frame('fist')
        self.frame('fist', x=0.6)
        self.frame(None)
        self.frame(None)
        fake_mouse.mouseUp.assert_called_once()
        self.assertIsNone(self.app.previous_point)
        self.assertIsNone(self.app.smoother)
        self.assertIsNone(self.app.scroll_reference)
        self.assertEqual(self.app.cursor.remainder_x, 0)
        fake_mouse.move.reset_mock()
        self.frame('palm', x=0.9)
        self.frame('palm', x=0.9)
        fake_mouse.move.assert_not_called()

    def test_hand_loss_does_not_rearm_held_pinch(self):
        self.hold('left')
        self.frame(None)
        self.hold('left')
        fake_mouse.click.assert_called_once()
        self.hold('palm', 30)
        self.hold('left')
        self.assertEqual(fake_mouse.click.call_count, 2)

    def test_scroll_reference_cleared_by_pinch_and_loss(self):
        self.frame('scroll', y=0.3)
        self.frame('scroll', y=0.4)
        self.assertTrue(fake_mouse.scroll.called)
        self.frame('left')
        fake_mouse.scroll.reset_mock()
        self.frame('scroll', y=0.8)
        fake_mouse.scroll.assert_not_called()
        self.frame(None)
        self.frame('scroll', y=0.2)
        fake_mouse.scroll.assert_not_called()

    def test_stopping_hand_has_no_filter_tail(self):
        self.frame('palm', x=0.3)
        self.frame('palm', x=0.4)
        self.assertTrue(fake_mouse.move.called)
        fake_mouse.move.reset_mock()
        for _ in range(60):
            self.frame('palm', x=0.4)
        fake_mouse.move.assert_not_called()

    def test_stationary_tremor_and_no_residual_motion(self):
        self.frame('palm')
        for i in range(180):
            self.frame('palm', x=0.5 + (0.0005 if i % 2 else -0.0005))
        fake_mouse.move.assert_not_called()
        cursor = PhysicsCursor()
        cursor.update_relative(0.01, 0, 1 / 60)
        self.assertTrue(fake_mouse.move.called)
        cursor.update_relative(0, 0, 1 / 60)
        self.assertEqual((cursor.prev_dx, cursor.remainder_x), (0, 0))
        fake_mouse.move.reset_mock()
        cursor.update_relative(0.0001, 0.0001, 1 / 60)
        fake_mouse.move.assert_not_called()
        self.assertTrue(fake_mouse.FAILSAFE)

    def test_capture_failure_releases_drag_without_inference(self):
        self.app.running = True
        self.app.start_time = self.now
        self.app.cap = Mock()
        self.app.cap.read.return_value = (False, None)
        self.app.tracker = Mock()
        self.frame('fist')
        with patch.object(cv2, 'waitKey', return_value=ord('q')), patch.object(cv2, 'destroyAllWindows'):
            self.app.run()
        fake_mouse.mouseUp.assert_called_once()
        self.app.tracker.process.assert_not_called()
        self.assertIsNone(self.app.previous_point)

    def test_low_fps_pause_releases_drag_without_inference(self):
        import numpy as np
        self.app.running = True
        self.app.start_time = self.now - 3
        self.app.cap = Mock()
        self.app.cap.read.return_value = (True, np.zeros((20, 20, 3), dtype=np.uint8))
        self.app.tracker = Mock()
        self.frame('fist')
        # A frozen test clock gives dt=0/FPS=0, exercising the existing pause.
        with patch.object(cv2, 'waitKey', return_value=ord('q')), patch.object(cv2, 'imshow'), patch.object(cv2, 'destroyAllWindows'):
            self.app.run()
        fake_mouse.mouseUp.assert_called_once()
        self.app.tracker.process.assert_not_called()
        self.assertIsNone(self.app.previous_point)

    def test_failsafe_cleanup_on_loop_exception(self):
        self.app.running = True
        self.app.start_time = self.now
        self.app.cap = Mock()
        self.app.cap.read.side_effect = RuntimeError('capture failed')
        self.frame('fist')
        with patch.object(cv2, 'destroyAllWindows'), self.assertRaises(RuntimeError):
            self.app.run()
        fake_mouse.mouseUp.assert_called_once()
        self.app.cap.release.assert_called_once()


if __name__ == '__main__':
    unittest.main(verbosity=2)
