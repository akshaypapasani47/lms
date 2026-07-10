print("ROUTING FILE LOADED")
from django.urls import path
from . import consumers
from .consumers import TerminalConsumer

# websocket_urlpatterns = [

#     re_path(
#         r"ws/terminal/$",
#         consumers.TerminalConsumer.as_asgi()
#     ),

# ]
websocket_urlpatterns = [
    path("ws/terminal/", TerminalConsumer.as_asgi()),
]