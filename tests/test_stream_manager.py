import datetime
import unittest
from unittest import mock

from ledmatrix import ImageFrame, CommandFrame, Commands, StreamManager, NoDataException


class TestReceiveData(unittest.TestCase):
    @mock.patch("ledmatrix.LEDMatrix", autospec=True)
    @mock.patch("ledmatrix.TCPServer", autospec=True)
    def test_stream_manager_client_sync(self, mock_tcpserver, mock_ledmatrix):
        test_image = ImageFrame(pixels=bytearray(b"\xff" * 16 * 32 * 4), height=16, width=32)
        test_image.source =("1.1.1.1", 12345)
        mock_tcpserver.get_frame.return_value = test_image
        stream_manger = StreamManager(server=mock_tcpserver, leds=mock_ledmatrix)
        stream_manger.run()
        self.assertEqual(len(stream_manger.streams), 1)

        stream_manger.streams[0].last_packet = datetime.datetime.now() - datetime.timedelta(minutes=1)
        mock_tcpserver.get_frame.side_effect = NoDataException()
        stream_manger.run()
        self.assertEqual(len(stream_manger.streams), 0)

    @mock.patch("ledmatrix.LEDMatrix", autospec=True)
    @mock.patch("ledmatrix.TCPServer", autospec=True)
    def test_stream_manager_switch_to_higher_prio(self, mock_tcpserver, mock_ledmatrix):
        test_image = ImageFrame(pixels=bytearray(b"\xff" * 16 * 32 * 4), height=16, width=32)
        test_image.source = ("1.1.1.1", 12345)
        mock_tcpserver.get_frame.return_value = test_image
        stream_manger = StreamManager(server=mock_tcpserver, leds=mock_ledmatrix)
        stream_manger.run()
        self.assertEqual(len(stream_manger.streams), 1)

        test_image.source = ("1.1.1.2", 12345)
        mock_tcpserver.get_frame.return_value = test_image
        stream_manger.run()
        self.assertEqual(len(stream_manger.streams), 2)
        active_stream = stream_manger.get_active_stream()
        self.assertEqual(active_stream.client, ("1.1.1.1", 12345))

        test_command = CommandFrame(command=Commands.SetPriority, value=10)
        test_command.source = ("1.1.1.2", 12345)
        mock_tcpserver.get_frame.return_value = test_command
        stream_manger.run()
        active_stream = stream_manger.get_active_stream()
        self.assertEqual(active_stream.client, ("1.1.1.2", 12345))


if __name__ == "__main__":
    unittest.main()
