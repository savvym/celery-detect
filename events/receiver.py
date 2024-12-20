import asyncio
import logging
import time
from threading import Event, Thread

from celery import Celery
from celery.events import EventReceiver
from celery.events.state import State
from channels.layers import get_channel_layer

from celery_detect.settings import MAX_TASKS, MAX_WORKERS

logger = logging.getLogger(__name__)

state = State(
    max_tasks_in_memory=MAX_TASKS,
    max_workers_in_memory=MAX_WORKERS,
)


class CeleryEventReceiver(Thread):
    """Thread for consuming events from a Celery cluster."""

    def __init__(self, app: Celery):
        super().__init__()
        self.app = app
        self._stop_signal = Event()
        self.queue_name = "celery_events"
        self.channel_layer = get_channel_layer()
        self.receiver: EventReceiver | None = None

    def run(self) -> None:
        logger.info("Starting event consumer...")
        while not self._stop_signal.is_set():
            try:
                self.consume_events()
            except (KeyboardInterrupt, SystemExit):
                break
            except Exception as e:
                logger.exception(f"Failed to capture events: '{e}', trying again in 10 seconds.")
                if not self._stop_signal.is_set():
                    time.sleep(10)

    def consume_events(self):
        logger.info("Connecting to celery cluster...")
        with self.app.connection() as connection:
            self.receiver = EventReceiver(
                channel=connection,
                app=self.app,
                handlers={
                    "*": self.on_event,
                },
            )
            logger.info("Starting to consume events...")
            self.receiver.capture(limit=None, timeout=None, wakeup=True)

    def on_event(self, event: dict) -> None:
        logger.debug(f"Received event: {event}")
        try:
            state.event(event)
        except KeyError as e:
            logger.warning(f"Failed to process event for unknown worker: '{e}'")
            return  # or handle the unknown worker event in another way

        asyncio.create_task(self.channel_layer.group_send(self.queue_name, {
            "type": "celery_event",
            "event": event,
        }))
        if self._stop_signal.is_set():
            raise KeyboardInterrupt("Stop signal received")

    def stop(self) -> None:
        logger.info("Stopping event consumer...")
        if self.receiver is not None:
            self.receiver.should_stop = True
        self._stop_signal.set()
        self.join()
