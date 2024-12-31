import logging

from celery import Celery

logger = logging.getLogger(__name__)
_celery_app_cache: Celery | None = None


def get_celery_app():
    global _celery_app_cache
    if _celery_app_cache is not None:
        return _celery_app_cache
    app = Celery(
        'celery_detect'
    )
    app.config_from_object('django.conf:settings', namespace='CELERY')
    _celery_app_cache = app
    return app
