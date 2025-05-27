from django.contrib import admin
from django.urls import path, include
from pages import views as pages_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('rentals.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path('about/', pages_views.about_view, name='about'),
    path('contact/', pages_views.contact_view, name='contact_us'),
    path('accounts/', include('allauth.urls')),
    path('summernote/', include('django_summernote.urls')),
]

urlpatterns += [
    path('login/', RedirectView.as_view(url='/accounts/login/', permanent=True)),
    path('logout/', RedirectView.as_view(url='/accounts/logout/', permanent=True)),
    path('register/', RedirectView.as_view(url='/accounts/signup/', permanent=True)),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
