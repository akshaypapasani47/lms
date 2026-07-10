from django.urls import path
from . import views

urlpatterns = [

    path('', views.terminal_home, name='terminal_home'),

    path(
        'run-command/',
        views.run_command,
        name='run_command'
    ),
    path(
        '',
        views.terminal_home,
        name='terminal_home'
    ),

    path(
        'login/',
        views.terminal_login,
        name='terminal_login'
    ),

    path(
        'run-command/',
        views.run_command,
        name='run_command'
    ),

    path(
    'logout/',
    views.terminal_logout,
    name='terminal_logout'
    ),
]