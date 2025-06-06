from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from rentals.models import Booking
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from .models import ContactMessage
from pages.forms import ContactForm
import json
from django.conf import settings
import stripe


@login_required(login_url='/account/login/')
def profile_view(request):
    user = request.user
    bookings = Booking.objects.filter(primary_driver=user).order_by('-start_date')
    messages_list = ContactMessage.objects.filter(user=user).order_by('-submitted_at')

    # Determine action from query params: create, edit, delete
    action = request.GET.get('action')
    msg_id = request.GET.get('msg_id')

    form = None
    delete_message = None

    if action == 'edit' and msg_id:
        # Editing an existing message
        msg = get_object_or_404(ContactMessage, pk=msg_id, user=user)
        if request.method == 'POST':
            form = ContactForm(request.POST, instance=msg)
            if form.is_valid():
                form.save()
                messages.success(request, "Message updated successfully!")
                return redirect('profile')
            else:
                messages.error(request, "Please fix the errors below.")
        else:
            form = ContactForm(instance=msg)

    elif action == 'delete' and msg_id:
        # Deleting an existing message
        delete_message = get_object_or_404(ContactMessage, pk=msg_id, user=user)
        if request.method == 'POST':
            delete_message.delete()
            messages.success(request, "Message deleted successfully!")
            return redirect('profile')

    else:
        # Creating a new message or just viewing profile
        if request.method == 'POST':
            form = ContactForm(request.POST)
            if form.is_valid():
                new_msg = form.save(commit=False)
                new_msg.user = user
                new_msg.save()
                messages.success(request, "Message sent successfully!")
                return redirect('profile')
            else:
                messages.error(request, "Please fix the errors below.")
        else:
            form = ContactForm()

    return render(request, 'accounts/profile.html', {
        'bookings': bookings,
        'messages': messages_list,
        'form': form,
        'delete_message': delete_message,
        'action': action,
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
