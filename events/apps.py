# events/apps.py

import logging
from django.apps import AppConfig
import threading
from celery_detect.celery_app import get_celery_app
from events.celery_events import start_event_listener
from events.receiver import CeleryEventReceiver


logger = logging.getLogger(__name__)


class EventsConfig(AppConfig):
    name = 'events'

    def ready(self):
        """
        在 Django 启动时，启动 Celery 事件监听器
        """
        # 使用线程异步启动事件监听器
        app = get_celery_app()
        consumer = CeleryEventReceiver(app)

        consumer.start()