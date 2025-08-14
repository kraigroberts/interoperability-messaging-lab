"""
ZeroMQ Subscriber for normalized tactical messages.
"""

import json
from threading import Event, Thread
from typing import Any, Callable, Optional

import zmq


class MessageSubscriber:
    """
    Subscribes to normalized tactical messages via ZeroMQ SUB socket.
    """

    def __init__(self, connect_address: str = "tcp://localhost:5555",
                 topics: Optional[list] = None):
        """
        Initialize the subscriber.

        Args:
            connect_address: ZeroMQ connect address (default: tcp://localhost:5555)
            topics: List of topics to subscribe to (default: ["tactical"])
        """
        self.connect_address = connect_address
        self.topics = topics or ["tactical"]
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(connect_address)

        # Subscribe to topics
        for topic in self.topics:
            self.socket.setsockopt_string(zmq.SUBSCRIBE, topic)

        self.running = False
        self.stop_event = Event()
        self.message_count = 0
        self.message_handler: Optional[Callable[[dict[str, Any]], None]] = None

    def set_message_handler(self, handler: Callable[[dict[str, Any]], None]) -> None:
        """
        Set a custom message handler function.

        Args:
            handler: Function that takes a message dictionary and processes it
        """
        self.message_handler = handler

    def default_message_handler(self, message: dict[str, Any]) -> None:
        """
        Default message handler that prints messages.

        Args:
            message: Normalized message dictionary
        """
        self.message_count += 1
        print(f"\n📡 Message #{self.message_count}")
        print(f"   Source: {message.get('source_format', 'unknown')}")
        print(f"   Type: {message.get('type', 'unknown')}")
        print(f"   ID: {message.get('id', 'N/A')}")

        # Show position if available
        position = message.get('position', {})
        if position.get('lat') and position.get('lon'):
            print(f"   Position: {position['lat']:.4f}, {position['lon']:.4f}")

        # Show time if available
        time_info = message.get('time', {})
        if time_info.get('reported'):
            print(f"   Time: {time_info['reported']}")

        # Show details if available
        detail = message.get('detail', {})
        if detail:
            print(f"   Details: {detail}")

        print("-" * 50)

    def start_receiving(self, timeout: Optional[float] = None) -> None:
        """
        Start receiving messages.

        Args:
            timeout: Timeout in seconds (None for no timeout)
        """
        if self.running:
            print("Subscriber is already running")
            return

        self.running = True
        self.stop_event.clear()
        print(f"Started receiving messages from {self.connect_address}")
        print(f"Subscribed to topics: {', '.join(self.topics)}")
        print("Press Ctrl+C to stop\n")

        try:
            while not self.stop_event.is_set():
                try:
                    # Set socket timeout if specified
                    if timeout is not None:
                        self.socket.setsockopt(zmq.RCVTIMEO, int(timeout * 1000))

                    # Receive message
                    message_str = self.socket.recv_string()

                    # Parse topic and message
                    if ' ' in message_str:
                        _, json_data = message_str.split(' ', 1)
                    else:
                        json_data = message_str

                    try:
                        message = json.loads(json_data)

                        # Use custom handler or default
                        if self.message_handler:
                            self.message_handler(message)
                        else:
                            self.default_message_handler(message)

                    except json.JSONDecodeError as e:
                        print(f"Error parsing message JSON: {e}")
                        print(f"Raw message: {json_data}")

                except zmq.Again:
                    # Timeout occurred
                    if timeout is not None:
                        continue
                    else:
                        break

        except KeyboardInterrupt:
            print("\nReceived interrupt signal")
        finally:
            self.stop_receiving()

    def start_receiving_async(self, timeout: Optional[float] = None) -> None:
        """
        Start receiving messages in a separate thread.

        Args:
            timeout: Timeout in seconds (None for no timeout)
        """
        if self.running:
            print("Subscriber is already running")
            return

        def receive_worker():
            self.start_receiving(timeout)

        self.receive_thread = Thread(target=receive_worker, daemon=True)
        self.receive_thread.start()

    def stop_receiving(self) -> None:
        """Stop receiving messages."""
        if self.running:
            self.stop_event.set()
            self.running = False
            print(f"Stopped receiving messages. Total received: {self.message_count}")

    def get_stats(self) -> dict[str, Any]:
        """
        Get subscriber statistics.

        Returns:
            Dictionary with subscriber statistics
        """
        return {
            "message_count": self.message_count,
            "running": self.running,
            "connect_address": self.connect_address,
            "topics": self.topics
        }

    def close(self) -> None:
        """Close the subscriber and clean up resources."""
        self.stop_receiving()
        self.socket.close()
        self.context.term()
        print("Subscriber closed")


def create_subscriber(connect_address: str = "tcp://localhost:5555",
                     topics: Optional[list] = None) -> MessageSubscriber:
    """
    Factory function to create a message subscriber.

    Args:
        connect_address: ZeroMQ connect address
        topics: List of topics to subscribe to

    Returns:
        Configured MessageSubscriber instance
    """
    return MessageSubscriber(connect_address, topics)
