"""
Contacts URL configuration.
"""
from django.urls import path

from . import views

app_name = "contacts"

urlpatterns = [
    path("", views.index, name="index"),
    path("create/", views.create, name="create"),
    path("<str:public_id>/", views.show, name="show"),
    path("<str:public_id>/edit/", views.edit, name="edit"),
    path("<str:public_id>/delete/", views.delete, name="delete"),
]
