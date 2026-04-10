"""
Identity URL configuration.

All routes serve Identity pages (CRM Contact has been eliminated).
"""

from django.urls import path

from . import views

app_name = "identities"

urlpatterns = [
    path("", views.index, name="index"),
    path("create/", views.create, name="create"),
    path("<str:public_id>/", views.show, name="show"),
    path("<str:public_id>/edit/", views.edit, name="edit"),
    path("<str:public_id>/delete/", views.delete, name="delete"),
    # JSON API endpoints (expand-on-demand + manual recalculation)
    path("<str:public_id>/expand/", views.expand, name="expand"),
    path(
        "<str:public_id>/recalculate/", views.recalculate_lifecycle, name="recalculate"
    ),
]
