from django.shortcuts import render
from .models import Campervan, Booking

def home(request):
    van = Campervan.objects.first()
    bookings = Booking.objects.filter(campervan=van)

    # Prepare booked date ranges to pass to the template
    booked_dates = []
    for booking in bookings:
        booked_dates.append({
            'start': booking.start_date.isoformat(),
            'end': booking.end_date.isoformat(),
        })

    return render(request, 'home.html', {'van': van, 'booked_dates': booked_dates})