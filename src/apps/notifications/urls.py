"""
Notifications URL configuration.
"""
from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.index, name="index"),
    path("<str:public_id>/read/", views.mark_read, name="mark-read"),
    path("mark-all-read/", views.mark_all_read, name="mark-all-read"),
]
