"""
Billing URL configuration.
"""
from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("", views.index, name="index"),
    path("checkout/<str:price_id>/", views.checkout, name="checkout"),
    path("success/", views.success, name="success"),
    path("cancel/", views.cancel, name="cancel"),
    path("portal/", views.portal, name="portal"),
]
