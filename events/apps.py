import logging
from django.apps import AppConfig


logger = logging.getLogger(__name__)


class EventsConfig(AppConfig):
    name = 'events'
