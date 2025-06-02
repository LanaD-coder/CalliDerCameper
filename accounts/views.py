from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rentals.models import Booking
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
import json


@login_required(login_url='/account/login/')
def profile_view(request):
    user = request.user
    bookings = Booking.objects.filter(primary_driver=user).order_by('-start_date')

    return render(request, 'accounts/profile.html', {
        'bookings': bookings,
    })



@csrf_exempt
def webhook_receiver(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Invalid method")

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    # TODO: Validate webhook signature/token if provided

    # Process the payload data
    event_type = payload.get('event')
    if event_type == 'booking_paid':
        booking_id = payload.get('booking_id')

    return JsonResponse({"status": "success"})
