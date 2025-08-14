"""
ZeroMQ Publisher for normalized tactical messages.
"""

import json
import time
from pathlib import Path
from threading import Event, Thread
from typing import Any, Union

import zmq

# Import with fallback for different execution contexts
try:
    from ..parsers.cot_parser import parse_cot_xml
    from ..parsers.vmf_parser import parse_vmf_binary
    from ..transforms.normalize_schema import normalize_message
    from ..transforms.validate import validate_normalized
except ImportError:
    # Fallback for when running as script
    from parsers.cot_parser import parse_cot_xml  # type: ignore
    from parsers.vmf_parser import parse_vmf_binary  # type: ignore
    from transforms.normalize_schema import normalize_message  # type: ignore
    from transforms.validate import validate_normalized  # type: ignore


class MessagePublisher:
    """
    Publishes normalized tactical messages via ZeroMQ PUB socket.
    """

    def __init__(self, bind_address: str = "tcp://*:5555"):
        """
        Initialize the publisher.

        Args:
            bind_address: ZeroMQ bind address (default: tcp://*:5555)
        """
        self.bind_address = bind_address
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(bind_address)
        self.running = False
        self.stop_event = Event()

        # Give the socket time to bind
        time.sleep(0.1)

    def publish_message(self, message: dict[str, Any], topic: str = "tactical") -> None:
        """
        Publish a single normalized message.

        Args:
            message: Normalized message dictionary
            topic: Message topic (default: "tactical")
        """
        try:
            # Validate the message before publishing
            validate_normalized(message)

            # Publish with topic and message
            message_data = json.dumps(message, ensure_ascii=False)
            self.socket.send_string(f"{topic} {message_data}")

        except Exception as e:
            print(f"Error publishing message: {e}")

    def publish_from_file(self, file_path: Union[str, Path], format_type: str) -> int:
        """
        Parse and publish messages from a file.

        Args:
            file_path: Path to the input file
            format_type: Message format ("cot" or "vmf")

        Returns:
            Number of messages published
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        data = file_path.read_bytes()
        count = 0

        try:
            if format_type == "cot":
                parsed = parse_cot_xml(data)
            elif format_type == "vmf":
                parsed = parse_vmf_binary(data)
            else:
                raise ValueError(f"Unsupported format: {format_type}")

            normalized = normalize_message(parsed)
            self.publish_message(normalized)
            count = 1

        except Exception as e:
            print(f"Error processing file {file_path}: {e}")

        return count

    def publish_from_files(self, file_paths: list[Union[str, Path]], format_type: str,
                          delay: float = 1.0) -> int:
        """
        Parse and publish messages from multiple files with delay.

        Args:
            file_paths: List of file paths
            format_type: Message format ("cot" or "vmf")
            delay: Delay between files in seconds

        Returns:
            Total number of messages published
        """
        total_count = 0

        for file_path in file_paths:
            count = self.publish_from_file(file_path, format_type)
            total_count += count

            if count > 0:
                print(f"Published {count} message(s) from {file_path}")

            if delay > 0 and file_path != file_paths[-1]:  # Don't delay after last file
                time.sleep(delay)

        return total_count

    def start_streaming(self, file_paths: list[Union[str, Path]], format_type: str,
                       delay: float = 1.0) -> None:
        """
        Start streaming messages in a separate thread.

        Args:
            file_paths: List of file paths to stream
            format_type: Message format ("cot" or "vmf")
            delay: Delay between messages in seconds
        """
        if self.running:
            print("Publisher is already running")
            return

        self.running = True
        self.stop_event.clear()

        def stream_worker() -> None:
            while not self.stop_event.is_set():
                for file_path in file_paths:
                    if self.stop_event.is_set():
                        break

                    try:
                        count = self.publish_from_file(file_path, format_type)
                        if count > 0:
                            print(f"Streamed {count} message(s) from {file_path}")

                        if delay > 0:
                            time.sleep(delay)

                    except Exception as e:
                        print(f"Error streaming from {file_path}: {e}")

                # Loop back to start if not stopped
                if not self.stop_event.is_set():
                    print("Restarting message stream...")

        self.stream_thread = Thread(target=stream_worker, daemon=True)
        self.stream_thread.start()
        print(f"Started streaming {len(file_paths)} file(s) with {delay}s delay")

    def stop_streaming(self) -> None:
        """Stop the streaming thread."""
        if self.running:
            self.stop_event.set()
            self.running = False
            print("Stopped message streaming")

    def close(self) -> None:
        """Close the publisher and clean up resources."""
        self.stop_streaming()
        self.socket.close()
        self.context.term()
        print("Publisher closed")


def create_publisher(bind_address: str = "tcp://*:5555") -> MessagePublisher:
    """
    Factory function to create a message publisher.

    Args:
        bind_address: ZeroMQ bind address

    Returns:
        Configured MessagePublisher instance
    """
    return MessagePublisher(bind_address)
