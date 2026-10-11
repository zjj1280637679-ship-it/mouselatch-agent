"""Pure invariants: no Chromium needed."""
import unittest
from mouselatch.model import MouseState, InvalidTransition

class TestMouseState(unittest.TestCase):
    def test_move_observe_turn_do_not_release(self):
        s = MouseState()
        s.press()
        for i in range(20):
            s.move(i * 5, i)
            self.assertEqual(s.observe()["held"], ["left"])
            s.agent_turn_end()
            self.assertEqual(s.held, {"left"})
            self.assertEqual(s.up_count, 0)
        s.release()
        self.assertEqual((s.down_count, s.up_count), (1, 1))

    def test_reject_illegal_transitions(self):
        s = MouseState()
        with self.assertRaises(InvalidTransition):
            s.release()
        s.press()
        with self.assertRaises(InvalidTransition):
            s.press()

    def test_abort_releases_without_double_up(self):
        s = MouseState()
        s.press("left")
        s.press("right")
        s.abort()
        self.assertFalse(s.held)
        self.assertEqual((s.down_count, s.up_count), (2, 2))
        s.abort()
        self.assertEqual(s.up_count, 2)

if __name__ == "__main__":
    unittest.main()
