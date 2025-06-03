from django.contrib import admin
from django.urls import path, include
from pages import views as pages_views
from rentals import views as rentals_views
from accounts import views as accounts_views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('', rentals_views.home, name='home'),
    path('admin/', admin.site.urls),
    path('/', include('rentals.urls')),
    path('pages/', include('pages.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path('about/', pages_views.about_view, name='about'),
    path('contact/', pages_views.contact_view, name='contact_us'),
    path('information/', pages_views.information_view, name='info'),
    path('videos/', pages_views.videos_view, name='vids_pics'),
    path('accounts/', include('allauth.urls')),
    path('account/', include('accounts.urls')),
    path('summernote/', include('django_summernote.urls')),
]

urlpatterns += [
    path('login/', RedirectView.as_view(url='/accounts/login/', permanent=True)),
    path('logout/', RedirectView.as_view(url='/accounts/logout/', permanent=True)),
    path('register/', RedirectView.as_view(url='/accounts/signup/', permanent=True)),
    path('profile/', accounts_views.profile_view, name='profile'),

]

handler404 = 'pages.views.custom_404'
handler500 = 'pages.views.custom_500'
handler403 = 'pages.views.custom_403'
handler400 = 'pages.views.custom_400'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
