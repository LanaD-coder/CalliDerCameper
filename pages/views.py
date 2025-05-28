from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactForm
from .models import FAQ, CampingDestination
from datetime import datetime



def about_view(request):
    destinations = CampingDestination.objects.all()
    return render(request, 'pages/about.html', {'destinations': destinations})


def information_view(request):
    return render(request, 'pages/information.html')


def videos_view(request):
    return render(request, 'pages/videos.html')


def contact_view(request):
    faqs = FAQ.objects.all()
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Your message has been sent!")
        return redirect('contact')
    return render(request, 'pages/contact.html', {'form': form, 'faqs': faqs})


def impressum(request):
    return render(request, "legal/impressum.html", {"year": datetime.now().year})

def datenschutz(request):
    return render(request, "legal/datenschutz.html", {"year": datetime.now().year})