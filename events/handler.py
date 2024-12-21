import asyncio
import os
import time
from asyncio import CancelledError
from django.conf import settings
from events.receiver import CeleryEventReceiver
from events.broadcaster import EventBroadcaster
from celery_detect.celery_app import get_celery_app
import logging

logger = logging.getLogger(__name__)

def startup_handler():
    logger.info("Welcome to Celery Insights!")
    # Update timezone
    os.environ["TZ"] = settings.TIME_ZONE
    time.tzset()
    asyncio.run(start_event_system())

async def start_event_system():
    # Start consuming events
    celery_app = get_celery_app()
    event_consumer = CeleryEventReceiver(celery_app)
    event_consumer.start()

    # Start broadcasting events
    listener = EventBroadcaster(event_consumer.queue)
    listener.start()

    try:
        # Let the system run indefinitely until stopped
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour (or adjust as needed)
    except (KeyboardInterrupt, SystemExit, CancelledError):
        logger.info("Stopping server...")
    finally:
        event_consumer.stop()
        listener.stop()
        logger.info("Goodbye! See you soon.")
