# urls.py
from django.urls import path
from . import views


urlpatterns = [
    path('info/', views.get_server_info),
    path('clients/', views.get_clients),
    path('clear/', views.clear_state),
    path('download-debug-bundle/', views.download_debug_bundle),
]