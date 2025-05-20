from django.shortcuts import get_object_or_404, render
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

    lang = request.GET.get('lang', 'en')

    return render(request, 'home.html', {'van': van, 'booked_dates': booked_dates, 'lang': lang})


def campervan_detail(request, pk):
    campervan = get_object_or_404(Campervan, pk=pk)
    images = campervan.images.all()
    return render(request, 'campervan_detail.html', {'van': campervan, 'van_images': images})
