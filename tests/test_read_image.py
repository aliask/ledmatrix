import unittest

import sys, os
testdir = os.path.dirname(__file__)
srcdir = '../ledmatrix'
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))

from ledmatrix import LEDMatrix

class TestImage(unittest.TestCase):

  def test_read_image_to_frame(self):
    self.assertEqual(1, 1, "OK")

if __name__ == '__main__':
    unittest.main()