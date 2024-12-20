# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_tasks, name='get_tasks'),
    path('<str:task_id>/', views.get_task_detail, name='get_task_detail'),
    path('<str:task_id>/result/', views.get_task_result, name='get_task_result'),
]