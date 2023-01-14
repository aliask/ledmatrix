import struct
import unittest

from ledmatrix.network_frame import ImageFrame, CommandFrame, Command, parse_frame, FrameException

TEST_BRIGHTNESS_CMD = struct.pack(
  "HBB",
  CommandFrame.IDENT,
  Command.SetBrightness.value,
  123
)
TEST_IMAGE_FRAME = struct.pack(
  "HHHHBBBBBBBB",
  ImageFrame.IDENT,   # Image Frame Identifier
  1,                  # Height
  2,                  # Width
  8,                  # Data Length
  255, 0, 255, 255,   # Magenta Pixel
  255, 0, 255, 255    # Magenta Pixel
)

class TestNetworkFrame(unittest.TestCase):
    def test_imageframe(self):
        test_image = ImageFrame(pixels=b"\xff" * 16 * 32 * 4, height=16, width=32)
        self.assertIsInstance(test_image, ImageFrame)

    def test_parse_frame_set_brightness(self):
        test_command = parse_frame(TEST_BRIGHTNESS_CMD)
        self.assertIsInstance(test_command, CommandFrame)
        self.assertIsInstance(test_command.command, Command)
        self.assertEqual(test_command.command, Command.SetBrightness)
        self.assertEqual(test_command.value, 123)

    def test_parse_frame_set_priority(self):
        blob = bytes.fromhex("2143010f")
        test_command = parse_frame(blob)
        self.assertIsInstance(test_command, CommandFrame)
        self.assertIsInstance(test_command.command, Command)
        self.assertEqual(test_command.command, Command.SetPriority)
        self.assertEqual(test_command.value, 15)

    def test_parse_frame_invalid_command(self):
        blob = bytes.fromhex("2143120f")
        self.assertRaises(FrameException, parse_frame, blob)

    def test_parse_frame_invalid_ident(self):
        blob = bytes.fromhex("12340000")
        self.assertRaises(FrameException, parse_frame, blob)

    def test_parse_frame_image(self):
        test_frame = parse_frame(TEST_IMAGE_FRAME)
        self.assertIsInstance(test_frame, ImageFrame)
        self.assertEqual(test_frame.height, 1)
        self.assertEqual(test_frame.width, 2)
        self.assertEqual(test_frame.pixels, b"\xff\x00\xff\xff"*2)

    def test_parse_frame_image_too_short(self):
        blob = bytes.fromhex("3412010002000800ffffffffffffff")
        self.assertRaises(FrameException, parse_frame, blob)

    def test_parse_frame_image_too_long(self):
        blob = bytes.fromhex("3412010002000800ffffffffffffffffff")
        self.assertRaises(FrameException, parse_frame, blob)

    def test_image_frame_cast_to_bytes(self):
        test_frame = ImageFrame(height=1, width=2, pixels=b"\xff\x00\xff\xff"*2)
        self.assertEqual(bytes(test_frame), TEST_IMAGE_FRAME)

    def test_command_frame_cast_to_bytes(self):
        test_frame = CommandFrame(command=Command.SetBrightness, value=15)
        self.assertEqual(bytes(test_frame), bytes.fromhex("2143000f"))

if __name__ == "__main__":
    unittest.main()
