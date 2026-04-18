from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/play/(?P<game_uuid>[0-9a-f-]+)/$', consumers.GameConsumer.as_asgi()),
]
