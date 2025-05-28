from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rentals.models import Booking

@login_required(login_url='/account/login/')
def profile_view(request):
    user = request.user
    bookings = Booking.objects.filter(user=user).order_by('-start_date')

    return render(request, 'accounts/profile.html', {
        'bookings': bookings,
    })