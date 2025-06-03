from django.urls import path
from . import views

urlpatterns = [
    path('book/<int:pk>/', views.booking_page, name='booking_page'),
    path('ajax/create-booking/<int:pk>/', views.create_booking_ajax, name='create_booking_ajax'),
    path('api/campervan/<int:pk>/booked_dates/', views.booked_dates_api, name='booked_dates_api'),

]