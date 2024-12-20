# events/apps.py

import logging
from django.apps import AppConfig
import threading
from events.celery_events import start_event_listener

logger = logging.getLogger(__name__)


class EventsConfig(AppConfig):
    name = 'events'

    def ready(self):
        """
        在 Django 启动时，启动 Celery 事件监听器
        """
        # 使用线程异步启动事件监听器
        listener_thread = threading.Thread(target=start_event_listener)
        listener_thread.daemon = True  # 设置为守护线程
        listener_thread.start()
