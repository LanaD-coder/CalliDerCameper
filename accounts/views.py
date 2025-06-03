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
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponseBadRequest("Invalid payload")
    except stripe.error.SignatureVerificationError:
        return HttpResponseBadRequest("Invalid signature")

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        booking_number = session.get('metadata', {}).get('booking_number')

        if booking_number:
            try:
                booking = Booking.objects.get(booking_number=booking_number)
                booking.payment_status = 'paid'
                booking.status = 'active'
                booking.payment_reference = session.get('payment_intent')
                booking.save()
            except Booking.DoesNotExist:
                return JsonResponse({'error': 'Booking not found'}, status=404)

    return JsonResponse({"status": "success"})