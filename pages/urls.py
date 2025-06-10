from django.urls import path
from . import views

urlpatterns = [
    path("impressum/", views.impressum, name="impressum"),
    path("datenschutz/", views.datenschutz, name="datenschutz"),
    path("rental-info/", views.information_view, name="information")
]
