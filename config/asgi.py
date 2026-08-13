print("ASGI FILE LOADED")

import os

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings"
)

import django

django.setup()

from django.core.asgi import get_asgi_application

from channels.routing import (
    ProtocolTypeRouter,
    URLRouter
)

from channels.auth import AuthMiddlewareStack
import virtual_lab_v2.routing
from programming_lab.routing import (
    websocket_urlpatterns as programming_websocket_urlpatterns
)

application = ProtocolTypeRouter({
    "http":
        get_asgi_application(),

    "websocket":
        AuthMiddlewareStack(
            URLRouter(
                virtual_lab_v2.routing.websocket_urlpatterns
                +
                programming_websocket_urlpatterns
            )
        )
})



# print("ASGI FILE LOADED")
# import os

# os.environ.setdefault(
#     "DJANGO_SETTINGS_MODULE",
#     "config.settings"
# )

# import django

# django.setup()

# from channels.routing import (
#     ProtocolTypeRouter,
#     URLRouter
# )

# from channels.auth import AuthMiddlewareStack
# from channels.routing import ProtocolTypeRouter, URLRouter
# from django.core.asgi import get_asgi_application
# import virtual_lab_v2.routing

# from virtual_lab_v2.routing import (
#     websocket_urlpatterns
# )

# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             virtual_lab_v2.routing.websocket_urlpatterns
#         )
#     )
# })

# import os

# import django
# from channels.http import AsgiHandler
# from channels.routing import ProtocolTypeRouter

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
# django.setup()

# application = ProtocolTypeRouter(
#     {
#         "http": AsgiHandler(),
#         # Just HTTP for now. (We can add other protocols later.)
#     }
# )
