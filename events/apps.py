import logging
import os
import asyncio
from django.apps import AppConfig
from django.conf import settings

from celery_detect.celery_app import get_celery_app
from events.receiver import CeleryEventReceiver
from events.broadcaster import EventBroadcaster


logger = logging.getLogger(__name__)


class EventsConfig(AppConfig):
    name = 'events'

    def ready(self):
        logger.info("Welcome to Celery Insights!")

        # Update timezone
        os.environ["TZ"] = settings.TIME_ZONE

        asyncio.run(self.start_event_system())

    async def start_event_system(self):
        # Start consuming events
        celery_app = get_celery_app()
        event_consumer = CeleryEventReceiver(celery_app)
        event_consumer.start()

        # Start broadcasting events
        listener = EventBroadcaster(event_consumer.queue)
        listener.start()

        # Store references to consumers and broadcasters for cleanup later
        self._event_consumer = event_consumer
        self._listener = listener

    def handle_shutdown(self, sender, **kwargs):
        logger.info("Stopping server...")
        if hasattr(self, '_event_consumer'):
            self._event_consumer.stop()
        if hasattr(self, '_listener'):
            self._listener.stop()
        logger.info("Goodbye! See you soon.")