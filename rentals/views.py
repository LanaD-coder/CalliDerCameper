from django.shortcuts import get_object_or_404, render
from .models import Campervan, Booking, SeasonalRate
from datetime import timedelta
import json
from django.utils.translation import gettext as _


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

    date_prices_dict = get_date_prices_for_van(campervan)

    context = {
            'van': campervan,
            'van_images': images,
            'date_prices': json.dumps(date_prices_dict),  # JSON string
            # add other context vars like booked_dates, calendar_events, etc.
    }

    return render(request, 'home.html', context)
