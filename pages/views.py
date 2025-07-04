from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import ContactForm
from .models import FAQ
from rentals.models import Campervan
from datetime import datetime
from pages.models import CampingDestination


def about_view(request):
    campervan = get_object_or_404(Campervan, pk=1)
    images = campervan.images.all()
    return render(request, 'pages/about.html', {
        'campervan': campervan,
        'images': images,
    })

def information_view(request):
    return render(request, 'pages/information.html')


def videos_view(request):
    destinations = CampingDestination.objects.all()
    faqs = FAQ.objects.all()
    return render(request, 'pages/videos.html', {
        'destinations': destinations,
        'faqs': faqs,
    })

def contact_view(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, _("Your message has been sent!"))
        return redirect('contact')
    return render(request, 'pages/contact.html', {
        'form': form,
    })

def impressum(request):
    return render(request, "legal/impressum.html", {"year": datetime.now().year})

def datenschutz(request):
    return render(request, "legal/datenschutz.html", {"year": datetime.now().year})

def custom_404(request, exception):
    return render(request, 'errors/404.html', status=404)

def custom_500(request):
    return render(request, 'errors/500.html', status=500)

def custom_403(request, exception):
    return render(request, 'errors/403.html', status=403)

def custom_400(request, exception):
    return render(request, 'errors/400.html', status=400)