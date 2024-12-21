import logging
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer

from ws.models import ClientInfo

logger = logging.getLogger(__name__)


class WebsocketManager:
    def __init__(self, name: str):
        self.name = name
        self.active_connections = []

    def subscribe(self, websocket: AsyncWebsocketConsumer) -> None:
        logger.info(f"Client {websocket.scope['client']} subscribed to {self.name} websocket manager")
        self.active_connections.append(websocket)

    def unsubscribe(self, websocket: AsyncWebsocketConsumer) -> None:
        logger.info(f"Client {websocket.scope['client']} unsubscribed from {self.name} websocket manager")
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str) -> None:
        """Broadcasts a message to all active connections."""
        logger.info(f"Broadcasting message to {self.name} websocket manager")
        for connection in self.active_connections:
            await connection.send(text_data=message)

    def get_clients(self) -> list[ClientInfo]:
        """Returns a list of clients currently connected."""
        return [client.client_info for client in self.active_connections]


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
        # 在这里进一步处理收到的消息
        pass

    async def broadcast_message(self, event):
        message = event['message']
        await self.send(text_data=message)
