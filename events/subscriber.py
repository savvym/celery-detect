import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Union

from asgiref.sync import sync_to_async
from channels.layers import get_channel_layer
from django.db import close_old_connections

logger = logging.getLogger(__name__)
T = TypeVar("T")


class QueueSubscriber(Generic[T], ABC):
    def __init__(self, channel_name: str, name: str = None):
        self.channel_layer = get_channel_layer()
        self.channel_name = channel_name
        self.name = name or self.__class__.__name__
        self._stop_signal = False

    def start(self):
        sync_to_async(self._listen)()

    async def _listen(self) -> None:
        logger.info(f"Subscribing to events from {self.name!r}...")
        close_old_connections()
        while not self._stop_signal:
            try:
                # Here we receive an event from a channel
                event = await self.channel_layer.receive(self.channel_name)
                logger.debug(f"Received event from {self.name!r}: {event}")
                try:
                    await self.handle_event(event)
                except Exception as e:
                    logger.exception(f"Failed to handle event: {e}")
            except Exception as e:
                logger.exception(f"Receive loop encountered an error: {e}")

    @abstractmethod
    async def handle_event(self, event: T) -> None:
        raise NotImplementedError()

    def stop(self):
        logger.info(f"Stopping subscriber {self.name!r}...")
        self._stop_signal = True
