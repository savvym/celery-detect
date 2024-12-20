import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer

from ws.models import ClientInfo

logger = logging.getLogger(__name__)


class WebsocketManager:
    def __init__(self, name: str):
        self.name = name
        self.channel_layer = get_channel_layer()
        self.active_connections = []

    async def subscribe(self, websocket: AsyncWebsocketConsumer) -> None:
        logger.info(f"Client {websocket.scope['client']!r} subscribed to {self.name!r} websocket manager")
        self.active_connections.append(websocket)
        await self.channel_layer.group_add(self.name, websocket.channel_name)

    async def unsubscribe(self, websocket: AsyncWebsocketConsumer) -> None:
        logger.info(f"Client {websocket.scope['client']!r} unsubscribed from {self.name!r} websocket manager")
        self.active_connections.remove(websocket)
        await self.channel_layer.group_discard(self.name, websocket.channel_name)

    async def broadcast(self, message: str) -> None:
        await self.channel_layer.group_send(
            self.name,
            {
                'type': 'broadcast.message',
                'message': message,
            }
        )

    async def get_clients(self) -> list[ClientInfo]:
        clients = [await ClientInfo.from_scope(client.scope) for client in self.active_connections]
        return clients


class WebSocketConsumer(AsyncWebsocketConsumer):
    manager: WebsocketManager
    client_info: ClientInfo

    async def connect(self):
        self.client_info = await ClientInfo.from_scope(self.scope)
        await self.manager.subscribe(self)
        await self.accept()

    async def disconnect(self, close_code):
        await self.manager.unsubscribe(self)

    async def receive(self, text_data=None, bytes_data=None):
        message = text_data if text_data else bytes_data
        # 在这里进一步处理收到的消息
        pass

    async def broadcast_message(self, event):
        message = event['message']
        await self.send(text_data=message)
