import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class EventsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = 'events'
