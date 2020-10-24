import unittest

from ledmatrix import LEDMatrix, LedFrame

class TestImage(unittest.TestCase):

  def setUp(self):
    self.image_frame = LEDMatrix.loadImage('pattern.png')

  def test_read_image_is_frame(self):
    self.assertIsInstance(self.image_frame, LedFrame, "Failed to decode image - wrong type returned")

  def test_read_image_height(self):
    self.assertEqual(self.image_frame.height, 16, "Failed to decode image - wrong height read")

  def test_read_image_width(self):
    self.assertEqual(self.image_frame.width, 32, "Failed to decode image - wrong width read")

  def test_read_image_pixels(self):
    pixel_hash = hash(tuple(self.image_frame.pixels))
    self.assertEqual(pixel_hash, 758414819, "Failed to decode image - pixel data mismatch")

if __name__ == '__main__':
    unittest.main()