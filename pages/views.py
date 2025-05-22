from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactForm
from .models import FAQ, CampingDestination



def about_view(request):
    destinations = CampingDestination.objects.all()
    return render(request, 'pages/about.html', {'destinations': destinations})


def contact_view(request):
    faqs = FAQ.objects.all()
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Your message has been sent!")
        return redirect('contact')
    return render(request, 'pages/contact.html', {'form': form, 'faqs': faqs})