import logging
import time
from threading import Event, Thread

from celery import Celery
from celery.events import EventReceiver
from celery.events.state import State
from asgiref.sync import sync_to_async, async_to_sync

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
        self._stop_signal = Event()
        self.queue = async_to_sync(self._create_async_queue)()
        self.receiver: EventReceiver | None = None

    def start(self):
        logger.info("Starting event consumer...")
        self.thread = Thread(target=self.run)
        self.thread.start()

    def run(self) -> None:
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
                    "*": async_to_sync(self.on_event),
                },
            )
            logger.info("Starting to consume events...")
            self.receiver.capture(limit=None, timeout=None, wakeup=True)

    async def on_event(self, event: dict) -> None:
        logger.debug(f"Received event: {event}")
        state.event(event)
        await self.queue.put(event)
        if self._stop_signal.is_set():
            raise KeyboardInterrupt("Stop signal received")

    def stop(self) -> None:
        logger.info("Stopping event consumer...")
        if self.receiver is not None:
            self.receiver.should_stop = True
        self._stop_signal.set()
        self.thread.join()

    @sync_to_async
    def _create_async_queue(self):
        import queue
        return queue.Queue()


# 启动事件接收器
def start_event_receiver(app: Celery):
    receiver = CeleryEventReceiver(app)
    receiver.start()
    return receiver
