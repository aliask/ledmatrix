import unittest

from ledmatrix.network_frame import ImageFrame, CommandFrame, Command, parse_frame


class TestNetworkFrame(unittest.TestCase):
    def test_imageframe(self):
        test_image = ImageFrame(pixels=b"\xff" * 16 * 32 * 4, height=16, width=32)
        self.assertIsInstance(test_image, ImageFrame)

    def test_parse_frame_set_brightness(self):
        blob = bytes.fromhex("214301ff")
        test_command = parse_frame(blob)
        self.assertIsInstance(test_command, CommandFrame)
        self.assertIsInstance(test_command.command, Command)
        self.assertEqual(testcommand.command, Command.SetBrightness)
        self.assertEqual(testcommand.value, 255)



if __name__ == "__main__":
    unittest.main()
