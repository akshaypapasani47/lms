from django.urls import path

from .consumers import ProgrammingTerminalConsumer


websocket_urlpatterns = [

    path(
        "ws/programming-terminal/",
        ProgrammingTerminalConsumer.as_asgi()
    ),

]