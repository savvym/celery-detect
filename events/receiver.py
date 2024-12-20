import logging
import time
from threading import Event, Thread
from celery import Celery
from celery.events import EventReceiver
from celery.events.state import State
from channels.layers import get_channel_layer
from django.conf import settings
from asyncio import Queue

logger = logging.getLogger(__name__)

state = State(
    max_tasks_in_memory=settings.CELERY_MAX_TASKS,
    max_workers_in_memory=settings.CELERY_MAX_WORKERS,
)


class CeleryEventReceiver(Thread):
    """Thread for consuming events from a Celery cluster and broadcasting them to Django Channels."""

    def __init__(self, app: Celery):
        super().__init__()
        self.app = app
        self._stop_signal = Event()
        self.queue = Queue()
        self.receiver: EventReceiver | None = None
        self.channel_layer = get_channel_layer()  # 获取Django Channels的ChannelLayer

    def run(self) -> None:
        """线程运行方法，用于捕获和处理 Celery 事件"""
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
        """连接到 Celery 集群并捕获事件"""
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

    async def on_event(self, event: dict) -> None:
        """处理接收到的 Celery 事件"""
        logger.debug(f"Received event: {event}")
        state.event(event)  # 更新 Celery 状态
        self.queue.put_nowait(event)  # 将事件放入队列中
        await self.broadcast_event(event)  # 将事件广播到 Channels

        if self._stop_signal.is_set():
            raise KeyboardInterrupt("Stop signal received")

    async def broadcast_event(self, event: dict):
        """通过 Django Channels 将事件广播到 WebSocket"""
        try:
            # 发送事件到所有连接的消费者
            await self.channel_layer.group_send(
                "events_group",  # 事件广播的组名
                {
                    "type": "broadcast_message",  # 消息类型
                    "message": event,  # 消息内容
                }
            )
        except Exception as e:
            logger.exception(f"Failed to broadcast event: {e}")

    def stop(self) -> None:
        """停止事件消费线程"""
        logger.info("Stopping event consumer...")
        if self.receiver is not None:
            self.receiver.should_stop = True
        self._stop_signal.set()
        self.join()
