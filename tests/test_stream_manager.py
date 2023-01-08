import datetime
import unittest
from unittest import mock

from ledmatrix.network_frame import ImageFrame, CommandFrame, Command
from ledmatrix.stream_manager import StreamManager, Stream, DEFAULT_PRIORITY


class TestStreamManager(unittest.TestCase):
    @mock.patch("ledmatrix.LEDMatrix", autospec=True)
    @mock.patch("ledmatrix.tcpserver.TCPServer", autospec=True)
    @mock.patch("ledmatrix.udpserver.UDPServer", autospec=True)
    def test_stream_manager_handle_packet(self, mock_udpserver, mock_tcpserver, mock_ledmatrix):
        test_image = ImageFrame(pixels=b"\xff" * 16 * 32 * 4, height=16, width=32)
        test_image.source ="1.1.1.1"
        
        stream_manger = StreamManager(port=1245, timeout=5, leds=mock_ledmatrix)
        stream_manger.handle_packet(test_image)

        self.assertEqual(len(stream_manger.streams), 1)
        self.assertEqual(stream_manger.streams[0].is_active, True)

    @mock.patch("ledmatrix.LEDMatrix", autospec=True)
    @mock.patch("ledmatrix.tcpserver.TCPServer", autospec=True)
    @mock.patch("ledmatrix.udpserver.UDPServer", autospec=True)
    def test_stream_manager_sync_client(self, mock_udpserver, mock_tcpserver, mock_ledmatrix):
        stream_manger = StreamManager(port=1245, timeout=5, leds=mock_ledmatrix)
        little_while_ago = datetime.datetime.now() - datetime.timedelta(minutes=1)
        test_stream = Stream(client="1.1.1.1", priority=1, last_packet=little_while_ago, is_active=True)
        stream_manger.streams.append(test_stream)

        stream_manger.sync_clients()
        self.assertEqual(len(stream_manger.streams), 0)

    @mock.patch("ledmatrix.LEDMatrix", autospec=True)
    @mock.patch("ledmatrix.tcpserver.TCPServer", autospec=True)
    @mock.patch("ledmatrix.udpserver.UDPServer", autospec=True)
    def test_stream_manager_switch_to_higher_priority(self, mock_udpserver, mock_tcpserver, mock_ledmatrix):
        stream_manger = StreamManager(port=1245, timeout=5, leds=mock_ledmatrix)
        test_stream = Stream(client="1.1.1.1", priority=1, last_packet=datetime.datetime.now(), is_active=True)
        stream_manger.streams.append(test_stream)

        active_stream = stream_manger.get_active_stream()
        self.assertEqual(active_stream.client, "1.1.1.1")

        test_command = CommandFrame(Command.SetPriority, value=10)
        test_command.source = ("1.1.1.2", 12345)
        stream_manger.handle_packet(test_command)

        active_stream = stream_manger.get_active_stream()
        self.assertEqual(active_stream.client, "1.1.1.2")

    @mock.patch("ledmatrix.LEDMatrix", autospec=True)
    @mock.patch("ledmatrix.tcpserver.TCPServer", autospec=True)
    @mock.patch("ledmatrix.udpserver.UDPServer", autospec=True)
    def test_stream_manager_stays_when_new_client_with_same_prio(self, mock_udpserver, mock_tcpserver, mock_ledmatrix):
        stream_manger = StreamManager(port=1245, timeout=5, leds=mock_ledmatrix)
        test_stream = Stream(client="1.1.1.1", priority=DEFAULT_PRIORITY, last_packet=datetime.datetime.now(), is_active=True)
        stream_manger.streams.append(test_stream)

        active_stream = stream_manger.get_active_stream()
        self.assertEqual(active_stream.client, "1.1.1.1")

        test_image = ImageFrame(pixels=b"\xff" * 16 * 32 * 4, height=16, width=32)
        test_image.source = ("1.1.1.2", 12345)
        stream_manger.handle_packet(test_image)

        active_stream = stream_manger.get_active_stream()
        self.assertEqual(active_stream.client, "1.1.1.1")


if __name__ == "__main__":
    unittest.main()
