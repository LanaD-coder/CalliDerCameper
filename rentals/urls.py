from django.urls import path
from . import views
from .api_views import api_date_prices

urlpatterns = [
    path('book/<int:pk>/', views.booking_page, name='booking_page'),
    path('ajax/create-booking/<int:pk>/', views.create_booking_ajax, name='create_booking_ajax'),
    path('api/booked-dates/', views.booked_dates_api, name='booked_dates_api'),
    path('api/check-availability/', views.check_availability, name='check_availability'),
    path('api/date-prices/', api_date_prices, name='api_date_prices'),
]