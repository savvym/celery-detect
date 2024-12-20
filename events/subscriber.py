import logging
import asyncio
from abc import ABC, abstractmethod
from asyncio import Event, CancelledError, create_task
from channels.layers import get_channel_layer
from typing import Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class QueueSubscriber(Generic[T], ABC):
    def __init__(self, name: str | None = None):
        self.name = name or self.__class__.__name__
        self._stop_signal = Event()
        self._task = None
        self.channel_layer = get_channel_layer()
        self.queue_name = f"{self.__class__.__name__}_queue"

    def start(self):
        """Start the subscription and listen to events."""
        loop = asyncio.get_event_loop()  # 获取当前事件循环
        if loop.is_running():
            # 如果当前事件循环正在运行，创建异步任务
            self._task = loop.create_task(self._listen())
        else:
            # 如果事件循环未运行，创建一个新的事件循环并启动任务
            loop.run_until_complete(self._listen())

    async def _listen(self) -> None:
        """Listen for events and process them."""
        logger.info(f"Subscribing to events from {self.name!r}...")
        while not self._stop_signal.is_set():
            try:
                event = await self.channel_layer.receive(self.queue_name)
                logger.debug(f"Received event from {self.name!r}: {event}")
                await self.handle_event(event)
            except CancelledError:
                break
            except Exception as e:
                logger.exception(f"Failed to handle event: {e}")

    @abstractmethod
    async def handle_event(self, event: T) -> None:
        """Override this method to handle specific events."""
        raise NotImplementedError()

    def stop(self):
        """Stop the subscriber."""
        logger.info(f"Stopping subscriber {self.name!r}...")
        self._stop_signal.set()
        if self._task.done():
            self._task.result()
        else:
            self._task.cancel()
