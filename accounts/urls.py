from django.urls import path
from rentals import views as rentals_views
from accounts import views as accounts_views
from .views import webhook_receiver

urlpatterns = [
    path('', rentals_views.home, name='home'),
    path('campervan/<int:pk>/', rentals_views.campervan_detail, name='campervan_detail'),
    path('profile/', accounts_views.profile_view, name='profile'),  # all message actions handled here
    path('webhook/receiver/', webhook_receiver, name='webhook_receiver'),
    path('payment-success/', rentals_views.payment_success, name='payment-success'),
    path('payment-cancel/', rentals_views.payment_cancel, name='payment-cancel'),
]
