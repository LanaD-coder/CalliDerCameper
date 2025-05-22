from django.contrib import admin
from django.urls import path, include
from accounts import views as accounts_views
from pages import views as pages_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('rentals.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path('about/', pages_views.about_view, name='about'),
    path('contact/', pages_views.contact_view, name='contact_us'),
    path('register/', accounts_views.register_view, name='register'),
    path('login/', accounts_views.login_view, name='login'),
    path('summernote/', include('django_summernote.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
