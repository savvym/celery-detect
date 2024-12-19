# ws/routing.py
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/events/$', consumers.EventsConsumer.as_asgi()),
    re_path(r'ws/raw_events/$', consumers.RawEventsConsumer.as_asgi()),
]