import unittest, hashlib

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
    pixel_hash = hashlib.md5()
    for pixel in self.image_frame.pixels:
      pixel_hash.update(str(pixel).encode())
    self.assertEqual(pixel_hash.hexdigest(), 'cd53df33f8e688061f61b3e8fbe1713c', "Failed to decode image - pixel data mismatch")

if __name__ == '__main__':
    unittest.main()