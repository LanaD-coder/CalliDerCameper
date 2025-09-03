from django.urls import path, register_converter
import uuid
from . import views
from .api_views import api_date_prices


class UUIDConverter:
    regex = '[0-9a-f-]{36}'

    def to_python(self, value):
        return str(value)

    def to_url(self, value):
        return str(value)

register_converter(UUIDConverter, 'uuid')

urlpatterns = [
    path('book/<int:pk>/', views.booking_page, name='booking_page'),
    path('ajax/create-booking/<int:pk>/', views.create_booking_ajax, name='create_booking_ajax'),
    path('api/booked-dates/', views.booked_dates_api, name='booked_dates_api'),
    path('api/check-availability/', views.check_availability, name='check_availability'),
    path('api/date-prices/', api_date_prices, name='api_date_prices'),
    path('api/check-auth/', views.check_auth, name="check_auth"),

    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/', views.booking_list, name='booking_list'),
    path('rentals/<int:pk>/edit/', views.booking_edit, name='booking_edit'),
    path('admin-panel/bookings/<int:pk>/delete/', views.booking_delete, name='booking_delete'),
    path('admin/handover-checklist/<str:booking_number>/', views.handover_checklist, name='handover_checklist'),
    path('admin/return-checklist/<str:booking_number>/', views.return_checklist, name='return_checklist'),
    path('checklist/<int:pk>/', views.checklist_detail, name='checklist_detail'),
    path('checklist/<int:pk>/pdf/', views.checklist_pdf, name='checklist_pdf'),
    path('checklist/<int:pk>/save/', views.save_checklist, name='save_checklist'),

     # BlockedDate CRUD
    path('admin/blocked-dates/add/', views.blocked_date_add, name='blocked_date_add'),
    path('admin/blocked-dates/<int:pk>/edit/', views.blocked_date_edit, name='blocked_date_edit'),
    path('admin/blocked-dates/<int:pk>/delete/', views.blocked_date_delete, name='blocked_date_delete'),
]