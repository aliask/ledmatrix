import unittest
import pytest

from ledmagic.ledmatrix import LEDMatrix

class LEDMatrixTests(unittest.TestCase):
    def setUp(self):
        self.led_matrix = LEDMatrix()

    # Mock() external_library_name
    #     def func1()
    #         return None
    #     def func2
    # did I call external+library_name.func with blah,blah,andblah
    @mock.patch("ledmagic.ledmatrix.external_library_name")
    def test_public_method_one_does_something(self, urllib3):
       self.led_matrix(stuff)
       assert # something, try to do only one assert per test

    def test_public_method_one_does_another_thing(self, urllib3):
       self.led_matrix(different_stuff)
       assert # another thing

    def test_context_and_explanation():

    def test_run_calls_libraries_with_correct_setup():