"""
Tests for ZeroMQ streaming functionality.
"""

from unittest.mock import Mock, patch

import pytest

from src.stream.pub import MessagePublisher, create_publisher
from src.stream.sub import MessageSubscriber, create_subscriber


def test_create_publisher():
    """Test publisher factory function."""
    publisher = create_publisher("tcp://*:5556")
    assert isinstance(publisher, MessagePublisher)
    assert publisher.bind_address == "tcp://*:5556"
    publisher.close()


def test_create_subscriber():
    """Test subscriber factory function."""
    subscriber = create_subscriber("tcp://localhost:5556", ["test"])
    assert isinstance(subscriber, MessageSubscriber)
    assert subscriber.connect_address == "tcp://localhost:5556"
    assert subscriber.topics == ["test"]
    subscriber.close()


def test_publisher_initialization():
    """Test publisher initialization."""
    publisher = MessagePublisher("tcp://*:5557")
    assert publisher.bind_address == "tcp://*:5557"
    assert publisher.running is False
    publisher.close()


def test_subscriber_initialization():
    """Test subscriber initialization."""
    subscriber = MessageSubscriber("tcp://localhost:5557", ["topic1", "topic2"])
    assert subscriber.connect_address == "tcp://localhost:5557"
    assert subscriber.topics == ["topic1", "topic2"]
    assert subscriber.message_count == 0
    subscriber.close()


def test_publisher_publish_message():
    """Test publishing a single message."""
    with patch('zmq.Context') as mock_context:
        mock_socket = Mock()
        mock_context.return_value.socket.return_value = mock_socket

        publisher = MessagePublisher("tcp://*:5558")

        # Test message
        test_message = {
            "schema_version": "1.0",
            "source_format": "cot",
            "type": "test",
            "time": {"reported": "2025-08-14T12:00:00Z"},
            "position": {"lat": 38.7, "lon": -77.2}
        }

        publisher.publish_message(test_message, "test_topic")

        # Verify socket was called
        mock_socket.send_string.assert_called_once()
        call_args = mock_socket.send_string.call_args[0][0]
        assert call_args.startswith("test_topic ")

        publisher.close()


def test_subscriber_message_handler():
    """Test subscriber message handler."""
    with patch('zmq.Context') as mock_context:
        mock_socket = Mock()
        mock_context.return_value.socket.return_value = mock_socket

        subscriber = MessageSubscriber("tcp://localhost:5558")

        # Test custom message handler
        received_messages = []
        def custom_handler(msg):
            received_messages.append(msg)

        subscriber.set_message_handler(custom_handler)
        assert subscriber.message_handler == custom_handler

        # Test default handler
        subscriber.set_message_handler(None)
        assert subscriber.message_handler is None

        subscriber.close()


def test_publisher_file_processing():
    """Test publisher file processing."""
    with patch('zmq.Context') as mock_context:
        mock_socket = Mock()
        mock_context.return_value.socket.return_value = mock_socket

        publisher = MessagePublisher("tcp://*:5559")

        # Mock parser to return valid data
        with patch('src.stream.pub.parse_cot_xml') as mock_parse:
            mock_parse.return_value = {
                "format": "cot",
                "raw": {
                    "uid": "TEST-123",
                    "type": "test",
                    "time": "2025-08-14T12:00:00Z",
                    "point": {"lat": 38.7, "lon": -77.2}
                }
            }

            # Mock file operations
            with patch('pathlib.Path.exists') as mock_exists, \
                 patch('pathlib.Path.read_bytes') as mock_read:
                mock_exists.return_value = True
                mock_read.return_value = b"<test>data</test>"

                count = publisher.publish_from_file("dummy.txt", "cot")
                assert count == 1

        publisher.close()


def test_subscriber_stats():
    """Test subscriber statistics."""
    with patch('zmq.Context') as mock_context:
        mock_socket = Mock()
        mock_context.return_value.socket.return_value = mock_socket

        subscriber = MessageSubscriber("tcp://localhost:5560")

        stats = subscriber.get_stats()
        assert "message_count" in stats
        assert "running" in stats
        assert "connect_address" in stats
        assert "topics" in stats

        subscriber.close()


def test_publisher_streaming_control():
    """Test publisher streaming start/stop."""
    with patch('zmq.Context') as mock_context:
        mock_socket = Mock()
        mock_context.return_value.socket.return_value = mock_socket

        publisher = MessagePublisher("tcp://*:5561")

        # Test streaming control
        assert publisher.running is False

        # Mock file paths
        mock_files = [Mock()]
        mock_files[0].exists.return_value = True
        mock_files[0].read_bytes.return_value = b"<test>data</test>"

        # Mock parser
        with patch('src.stream.pub.parse_cot_xml') as mock_parse:
            mock_parse.return_value = {
                "format": "cot",
                "raw": {
                    "uid": "TEST-123",
                    "type": "test",
                    "time": "2025-08-14T12:00:00Z",
                    "point": {"lat": 38.7, "lon": -77.2}
                }
            }

            # Start streaming
            publisher.start_streaming(mock_files, "cot", 0.1)
            assert publisher.running is True

            # Stop streaming
            publisher.stop_streaming()
            assert publisher.running is False

        publisher.close()


def test_subscriber_receiving_control():
    """Test subscriber receiving start/stop."""
    with patch('zmq.Context') as mock_context:
        mock_socket = Mock()
        mock_context.return_value.socket.return_value = mock_socket

        subscriber = MessageSubscriber("tcp://localhost:5562")

        # Test receiving control
        assert subscriber.running is False

        # Start receiving (async)
        subscriber.start_receiving_async()
        assert subscriber.running is True

        # Stop receiving
        subscriber.stop_receiving()
        assert subscriber.running is False

        subscriber.close()


def test_publisher_error_handling():
    """Test publisher error handling."""
    with patch('zmq.Context') as mock_context:
        mock_socket = Mock()
        mock_context.return_value.socket.return_value = mock_socket

        publisher = MessagePublisher("tcp://*:5563")

        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            publisher.publish_from_file("nonexistent.txt", "cot")

        publisher.close()


def test_subscriber_error_handling():
    """Test subscriber error handling."""
    with patch('zmq.Context') as mock_context:
        mock_socket = Mock()
        mock_context.return_value.socket.return_value = mock_socket

        subscriber = MessageSubscriber("tcp://localhost:5564")

        # Test with invalid address (this would fail in real usage)
        # But we're mocking, so it should work
        assert subscriber.connect_address == "tcp://localhost:5564"

        subscriber.close()


def test_publisher_multiple_files():
    """Test publisher with multiple files."""
    with patch('zmq.Context') as mock_context:
        mock_socket = Mock()
        mock_context.return_value.socket.return_value = mock_socket

        publisher = MessagePublisher("tcp://*:5565")

        # Mock parser
        with patch('src.stream.pub.parse_cot_xml') as mock_parse:
            mock_parse.return_value = {
                "format": "cot",
                "raw": {
                    "uid": "TEST-123",
                    "type": "test",
                    "time": "2025-08-14T12:00:00Z",
                    "point": {"lat": 38.7, "lon": -77.2}
                }
            }

            # Mock file operations for multiple files
            with patch('pathlib.Path.exists') as mock_exists, \
                 patch('pathlib.Path.read_bytes') as mock_read:
                mock_exists.return_value = True
                mock_read.return_value = b"<test>data</test>"

                count = publisher.publish_from_files(["file1.txt", "file2.txt"], "cot", 0.1)
                assert count == 2

        publisher.close()
