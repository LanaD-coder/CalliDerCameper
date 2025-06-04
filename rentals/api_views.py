from datetime import date, timedelta
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import SeasonalRate

def daterange(start_date, end_date):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)

def date_prices_for_year(year=None):
    if year is None:
        year = date.today().year

    # For simplicity, let's assume full year Jan 1 - Dec 31
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    # Get all seasonal rates once
    seasonal_rates = SeasonalRate.objects.all()

    date_prices = {}

    for single_date in daterange(start_date, end_date):
        # Find the rate that applies for this date (first matching rate)
        rate = None
        for seasonal_rate in seasonal_rates:
            if seasonal_rate.includes_date(single_date):
                rate = seasonal_rate.rate
                break

        if rate is not None:
            date_prices[single_date.isoformat()] = float(rate)

    return date_prices

@require_GET
def api_date_prices(request):
    year_param = request.GET.get('year')
    try:
        year = int(year_param) if year_param else None
    except ValueError:
        year = None

    data = date_prices_for_year(year)
    return JsonResponse(data)
