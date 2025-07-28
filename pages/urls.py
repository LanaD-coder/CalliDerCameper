from django.urls import path
from . import views
from .views import contact_view

urlpatterns = [
    path("impressum/", views.impressum, name="impressum"),
    path("datenschutz/", views.datenschutz, name="datenschutz"),
    path("rental-info/", views.information_view, name="information"),
    path('contact/', contact_view, name='contact'),
    path('videos/', views.videos_view, name='videos'),
]
