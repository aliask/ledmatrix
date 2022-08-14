import unittest
from unittest import mock
import struct
import select, socket

from ledmatrix import UDPServer, CommandFrame, ImageFrame, Commands

TEST_BRIGHTNESS_CMD = struct.pack(
  "HBB",
  CommandFrame.IDENT,
  Commands.SetBrightness.value,
  123
)
TEST_IMAGE_FRAME = struct.pack(
  "HHHHBBBB",
  ImageFrame.IDENT,   # Image Frame Identifier
  1,                  # Height
  1,                  # Width
  4,                  # Data Length
  255, 0, 255, 255    # Magenta Pixel
)

class TestReceiveData(unittest.TestCase):

  @mock.patch('socket.socket', autospec=True)
  def test_init_udpserver(self, mock_sock):
    server = UDPServer(port=1234, timeout=5)
    self.assertIsInstance(server, UDPServer)
    self.assertEqual(server.port, 1234)
    self.assertEqual(server.timeout, 5)

  @mock.patch.object(select, 'select')
  @mock.patch('socket.socket')
  @mock.patch.object(socket, 'getnameinfo')
  def test_get_frame_command(self, mock_getnameinfo, mock_sock, mock_select):
    fake_source = ('1.1.1.1', 12345)
    socket.socket().recvfrom.return_value = (TEST_BRIGHTNESS_CMD, fake_source)
    mock_getnameinfo.return_value = fake_source
    mock_select.return_value = ([], 0, 0)

    server = UDPServer(port=1234, timeout=5)
    server.start()
    network_frame = server.get_frame(1)

    self.assertIsInstance(network_frame, CommandFrame, "Failed to read network frame - wrong type returned")
    self.assertEqual(network_frame.source, fake_source)
    self.assertEqual(network_frame.command, Commands.SetBrightness)
    self.assertEqual(network_frame.value, 123)

  @mock.patch.object(select, 'select')
  @mock.patch('socket.socket')
  @mock.patch.object(socket, 'getnameinfo')
  def test_get_image_frame(self, mock_getnameinfo, mock_sock, mock_select):
    fake_source = ('1.1.1.1', 12345)
    socket.socket().recvfrom.returnvalue = (TEST_IMAGE_FRAME, fake_source)
    mock_getnameinfo.return_value = fake_source
    mock_select.return_value = ([], 0, 0)

    server = UDPServer(port=1234, timeout=5)
    server.start()
    network_frame = server.get_frame(1)

    self.assertIsInstance(network_frame, ImageFrame, "Failed to read network frame - wrong type returned")
    self.assertEqual(network_frame.source, fake_source)
    self.assertEqual(network_frame.height, 1)
    self.assertEqual(network_frame.width, 1)

if __name__ == '__main__':
    unittest.main()