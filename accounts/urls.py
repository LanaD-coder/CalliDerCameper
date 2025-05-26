from django.urls import path
from rentals import views

urlpatterns = [
    path('', views.home, name='home'),
    path('campervan/<int:pk>/', views.campervan_detail, name='campervan_detail'),
    path('campervan/<int:pk>/book/', views.book_campervan, name='book_campervan'),
]