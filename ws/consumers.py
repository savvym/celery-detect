import logging
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from ws.managers import events_manager, raw_events_manager

logger = logging.getLogger(__name__)


class BaseWebSocketConsumer(AsyncWebsocketConsumer):
    manager = None  # Define the manager in subclass

    async def connect(self):
        await self.accept()
        self.manager.subscribe(self)
        logger.info(f"Client {self.scope['client']} connected to {self.manager.name}")

    def disconnect(self, close_code):
        self.manager.unsubscribe(self)
        logger.info(f"Client {self.scope['client']} disconnected from {self.manager.name}")

    async def receive(self, text_data=None, bytes_data=None):
        try:
            message = text_data or bytes_data
            logger.debug(f"Client {self.scope['client']} sent message: {message}")
            # You can respond with a JSON message:
            response = {"code": 0, "message": "ok"}
            await self.send(text_data=json.dumps(response))
        except Exception as e:
            logger.error(f"Error processing received message from {self.scope['client']}: {e}")
            await self.send(text_data=json.dumps({"code": -1, "message": "error"}))


class EventsConsumer(BaseWebSocketConsumer):
    manager = events_manager


class RawEventsConsumer(BaseWebSocketConsumer):
    manager = raw_events_manager
