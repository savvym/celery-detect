import asyncio
import logging
from asyncio import Queue
from collections.abc import Iterable

from channels.generic.websocket import AsyncWebsocketConsumer

from ws.models import ClientInfo

logger = logging.getLogger(__name__)


class WebsocketManager:
    def __init__(self, name: str):
        self.name = name
        self.queue = Queue()
        self.active_connections: list[AsyncWebsocketConsumer] = []

    def subscribe(self, websocket: AsyncWebsocketConsumer) -> None:
        logger.info(f"Client {websocket.scope['client']!r} subscribed to {self.name!r} websocket manager")
        self.active_connections.append(websocket)

    def unsubscribe(self, websocket: AsyncWebsocketConsumer) -> None:
        logger.info(f"Client {websocket.scope['client']!r} unsubscribed from {self.name!r} websocket manager")
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str) -> None:
        results = await asyncio.gather(
            *[
                connection.send(text_data=message) for connection in self.active_connections
            ],
            return_exceptions=True
        )
        for result, connection in zip(results, self.active_connections):
            if isinstance(result, Exception):
                logger.exception(f"Failed to send message to client {connection.scope['client']!r}: {result}", exc_info=result)

    async def get_clients(self) -> Iterable[ClientInfo]:
        for client in self.active_connections:
            yield await ClientInfo.from_scope(client.scope)


class WebSocketConsumer(AsyncWebsocketConsumer):
    manager: WebsocketManager
    client_info: ClientInfo

    async def connect(self):
        self.client_info = await ClientInfo.from_scope(self.scope)
        self.manager.subscribe(self)
        await self.accept()

    async def disconnect(self, close_code):
        self.manager.unsubscribe(self)

    async def receive(self, text_data=None, bytes_data=None):
        message = text_data if text_data else bytes_data
        # You can process received message here if needed
        pass