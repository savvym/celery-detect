import logging
from django.apps import AppConfig
import threading
from events.handler import startup_handler

logger = logging.getLogger(__name__)


class EventsConfig(AppConfig):
    name = 'events'

    def ready(self):
        # We will call startup_handler in a new thread after Django starts.
        threading.Thread(target=startup_handler, daemon=True).start()