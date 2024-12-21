# urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_workers, name='get_workers'),
    path('/stats', views.get_worker_stats, name='get_worker_stats'),
    path('/registered', views.get_worker_registered, name='get_worker_registered'),
    path('/revoked', views.get_worker_revoked, name='get_worker_revoked'),
    path('/scheduled', views.get_worker_scheduled, name='get_worker_scheduled'),
    path('/reserved', views.get_worker_reserved, name='get_worker_reserved'),
    path('/active', views.get_worker_active, name='get_worker_active'),
    path('/queues', views.get_worker_queues, name='get_worker_queues'),
]
