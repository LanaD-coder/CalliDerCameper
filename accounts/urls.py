from django.urls import path
from rentals import views as rentals_views
from accounts import views as accounts_views

urlpatterns = [
    path('', rentals_views.home, name='home'),
    path('campervan/<int:pk>/', rentals_views.campervan_detail, name='campervan_detail'),
    path('campervan/<int:pk>/book/', rentals_views.book_campervan, name='book_campervan'),
    path('profile/', accounts_views.profile_view, name='profile'),
]
