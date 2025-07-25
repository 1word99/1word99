import logging
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class EventManager:
    """
    A centralized event manager for the Osmanli AI system.
    Allows components to subscribe to and publish events.
    """

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        logger.info("EventManager initialized.")

    def subscribe(self, event_type: str, listener: Callable) -> None:
        """
        Subscribes a listener function to an event type.

        Args:
            event_type: The type of event to listen for (e.g., "plugin_loaded", "error_occurred").
            listener: The function to call when the event is published.
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)
        logger.debug(f"Listener subscribed to event: {event_type}")

    def publish(self, event_type: str, **kwargs: Any) -> None:
        """
        Publishes an event, notifying all subscribed listeners.

        Args:
            event_type: The type of event to publish.
            **kwargs: Arbitrary keyword arguments to pass to the listeners.
        """
        if event_type in self._listeners:
            for listener in self._listeners[event_type]:
                try:
                    listener(**kwargs)
                    logger.debug(
                        f"Event '{event_type}' published to listener {listener.__name__}"
                    )
                except Exception as e:
                    logger.error(f"Error in event listener for '{event_type}': {e}")
        else:
            logger.debug(f"No listeners for event type: {event_type}")

    def self_test(self) -> bool:
        """Performs a self-test of the EventManager component."""
        logger.info("Running self-test for EventManager...")
        try:
            manager = EventManager()
            test_result = {"event_received": False, "data": None}

            def test_listener(data):
                test_result["event_received"] = True
                test_result["data"] = data

            manager.subscribe("test_event", test_listener)
            manager.publish("test_event", data="hello")

            if test_result["event_received"] and test_result["data"] == "hello":
                logger.info("EventManager self-test passed.")
                return True
            else:
                logger.error(
                    "EventManager self-test failed: Event not received or data incorrect."
                )
                return False
        except Exception as e:
            logger.error(f"EventManager self-test failed: {e}")
            return False
