import asyncio
import logging
import time
from celery import Celery
from celery.events import EventReceiver
from celery.events.state import State
from celery_detect.settings import MAX_TASKS, MAX_WORKERS
logger = logging.getLogger(__name__)

state = State(
    max_tasks_in_memory=MAX_TASKS,
    max_workers_in_memory=MAX_WORKERS,
)


class CeleryEventReceiver:
    """Class for consuming events from a Celery cluster."""

    def __init__(self, app: Celery):
        self.app = app
        self._stop_signal = asyncio.Event()
        self.queue = asyncio.Queue()
        self.receiver: EventReceiver | None = None

    async def start(self) -> None:
        logger.info("Starting event consumer...")
        while not self._stop_signal.is_set():
            try:
                await self.consume_events()
            except (KeyboardInterrupt, SystemExit):
                break
            except Exception as e:
                logger.exception(f"Failed to capture events: '{e}', trying again in 10 seconds.")
                if not self._stop_signal.is_set():
                    await asyncio.sleep(10)

    async def consume_events(self):
        logger.info("Connecting to celery cluster...")
        loop = asyncio.get_event_loop()
        with self.app.connection() as connection:
            self.receiver = EventReceiver(
                channel=connection,
                app=self.app,
                handlers={
                    "*": lambda event: loop.call_soon_threadsafe(self.on_event, event),
                },
            )
            logger.info("Starting to consume events...")
            while not self._stop_signal.is_set():
                self.receiver.capture(limit=None, timeout=None, wakeup=True)

    def on_event(self, event: dict) -> None:
        logger.debug(f"Received event: {event}")
        state.event(event)
        asyncio.create_task(self.queue.put(event))
        if self._stop_signal.is_set():
            raise KeyboardInterrupt("Stop signal received")

    async def stop(self) -> None:
        logger.info("Stopping event consumer...")
        self._stop_signal.set()
        if self.receiver is not None:
            self.receiver.should_stop = True