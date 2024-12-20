import logging
import os
import time
from django.apps import AppConfig
from django.core.cache import cache
from django.core.signals import request_started
from django.dispatch import receiver
from celery_detect.celery_app import get_celery_app
from django.conf import settings  # 确保正确导入
from events.broadcaster import EventBroadcaster
from events.receiver import CeleryEventReceiver
from threading import Thread

logger = logging.getLogger(__name__)


class EventsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = 'events'

    def ready(self):
        print("Welcome to Celery Insights in Django!")

        # Update timezone
        os.environ["TZ"] = settings.TIME_ZONE
        time.tzset()

        # Setup cache (assuming a suitable cache backend is defined in settings.py)
        cache.clear()

        # Start consuming events
        celery_app = get_celery_app()
        self.event_consumer = CeleryEventReceiver(celery_app)

        # Start the event consumer in a separate thread to avoid blocking the ready method
        self.event_consumer_thread = Thread(target=self.event_consumer.start)
        self.event_consumer_thread.start()

        # Create the event broadcaster
        self.listener = EventBroadcaster('celery_events')

        # Start the listener subscriber
        self.listener_thread = Thread(target=self.listener.start)
        self.listener_thread.start()

        # Register signal handlers
        request_started.connect(self.on_request_started)

        # Register shutdown handler for Django server stop
        import atexit
        atexit.register(self.shutdown)

    @receiver(request_started)
    def on_request_started(sender, **kwargs):
        logger.info("Request started...")

    def shutdown(self):
        logger.info("Stopping server...")
        self.event_consumer.stop()
        self.listener.stop()
        self.event_consumer_thread.join()
        self.listener_thread.join()
        logger.info("Goodbye! See you soon.")
