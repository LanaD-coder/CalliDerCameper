from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from .models import Campervan, Booking, SeasonalRate
from datetime import timedelta
from django.http import JsonResponse
import json
from django.utils.translation import gettext as _
from django.contrib import messages
from .forms import BookingForm


def home(request):
    van = Campervan.objects.first()
    bookings = Booking.objects.filter(campervan=van)
    seasonal_rates = SeasonalRate.objects.all()

    # Build booked date ranges as list of dicts with start and end
    booked_dates = []
    for booking in bookings:
        booked_dates.append({
            'start': booking.start_date.isoformat(),
            'end': booking.end_date.isoformat(),
        })

    calendar_events = []

    # Red background for booked dates (ranges)
    for bd in booked_dates:
        calendar_events.append({
            'start': bd['start'],
            'end': bd['end'],
            'title': _('Booked'),
            'display': 'background',
            'backgroundColor': '#f8d7da',
            'borderColor': '#dc3545',
        })

    # Blue background for seasonal rate ranges
    for season in seasonal_rates:
        calendar_events.append({
            'start': season.start.isoformat(),
            'end': (season.end + timedelta(days=1)).isoformat(),
            'title': f"${season.rate}/day",
            'display': 'background',
            'backgroundColor': '#d1ecf1',
            'borderColor': '#17a2b8',
        })

    date_prices = get_date_price_map()

    return render(request, 'home.html', {
        'van': van,
        'booked_dates': json.dumps(booked_dates),
        'calendar_events': json.dumps(calendar_events),
        'date_prices': json.dumps(date_prices),
    })

def get_date_price_map():
    date_prices = {}
    for rate in SeasonalRate.objects.all():
        current = rate.start
        while current <= rate.end:
            date_prices[current.strftime('%Y-%m-%d')] = float(rate.rate)
            current += timedelta(days=1)
    return date_prices

def campervan_detail(request, pk):
    campervan = get_object_or_404(Campervan, pk=pk)
    images = campervan.images.all()

    date_prices_dict = get_date_price_map()

    context = {
            'van': campervan,
            'van_images': images,
            'date_prices': json.dumps(date_prices_dict),

    }

    return render(request, 'home.html', context)


@login_required(login_url='/account/login/')
def book_campervan(request, pk):
    campervan = get_object_or_404(Campervan, pk=pk)

    initial_data = {}
    if 'start_date' in request.GET and 'end_date' in request.GET:
        initial_data['start_date'] = request.GET['start_date']
        initial_data['end_date'] = request.GET['end_date']

    if request.method == 'POST':
        form = BookingForm(request.POST, user=request.user, campervan=campervan)
        form.instance.campervan = campervan
        if form.is_valid():
            booking = form.save(commit=False)
            # campervan set in form.save(), so no need to set here again
            booking.save()
            messages.success(request, _('Booking confirmed!'))
            return redirect('campervan_detail', pk=campervan.pk)
    else:
        form = BookingForm(initial=initial_data, user=request.user, campervan=campervan)

    date_prices_dict = get_date_price_map()

    return render(request, 'rentals/booking_form.html', {
        'form': form,
        'campervan': campervan,
        'date_prices_json': json.dumps(date_prices_dict),
        })


def booked_dates_api(request, pk):
    campervan = get_object_or_404(Campervan, pk=pk)
    bookings = campervan.bookings.all()
    booked_ranges = [{'start': b.start_date.isoformat(), 'end': b.end_date.isoformat()} for b in bookings]
    return JsonResponse(booked_ranges, safe=False)
