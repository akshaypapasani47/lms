from django.urls import path

from .consumers import (
    VirtualLabTerminalConsumer,
    VirtualLabCodeRunnerConsumer,
)


websocket_urlpatterns = [

    # -------------------------------------------------
    # REAL VIRTUAL LAB TERMINAL
    # -------------------------------------------------

    path(
        "ws/virtuallab/<int:lab_id>/terminal/",
        VirtualLabTerminalConsumer.as_asgi(),
    ),

    # -------------------------------------------------
    # INTERACTIVE CODE RUNNER
    # -------------------------------------------------

    path(
        "ws/virtuallab/<int:lab_id>/run-code/",
        VirtualLabCodeRunnerConsumer.as_asgi(),
    ),
]