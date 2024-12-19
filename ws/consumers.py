import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from ws.managers import events_manager, raw_events_manager

logger = logging.getLogger(__name__)


class BaseWebSocketConsumer(AsyncWebsocketConsumer):
    manager = None  # Define the manager in subclass

    async def connect(self):
        await self.accept()
        self.manager.subscribe(self)
        logger.info(f"Client {self.scope['client']} connected to {self.manager.name}")

    async def disconnect(self, close_code):
        self.manager.unsubscribe(self)
        logger.info(f"Client {self.scope['client']} disconnected from {self.manager.name}")

    async def receive(self, text_data=None, bytes_data=None):
        message = text_data or bytes_data
        logger.warning(f"Client {self.scope['client']} sent message to {self.manager.name} manager: {message}")
        # Handle the received message (optional) here


class EventsConsumer(BaseWebSocketConsumer):
    manager = events_manager


class RawEventsConsumer(BaseWebSocketConsumer):
    manager = raw_events_manager