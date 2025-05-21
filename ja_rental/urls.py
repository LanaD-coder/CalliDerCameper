from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views
from pages import views as pages_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('rentals.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path('about/', pages_views.about_view, name='about'),
    path('register/', accounts_views.register_view, name='register'),
    path('login/', accounts_views.login_view, name='login'),
    path('admin/summernote/', include('django_summernote.urls')),
]
