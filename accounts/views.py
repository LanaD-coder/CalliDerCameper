from django.shortcuts import render


def register_view(request):
    return render(request, 'accounts/registration.html')

def login_view(request):
    return render(request, 'accounts/login.html')
