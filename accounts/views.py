from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from rentals.models import Booking, Invoice
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib import messages
from django.shortcuts import redirect
from .models import ContactMessage
from pages.forms import ContactForm
import json
from django.conf import settings
import stripe


@login_required(login_url='/account/login/')
def profile_view(request):
    user = request.user
    bookings = Booking.objects.filter(primary_driver=user).order_by('-start_date')
    invoices = Invoice.objects.filter(bookings__primary_driver=user).distinct().order_by('-issued_date')
    messages_list = ContactMessage.objects.filter(user=user).order_by('-submitted_at')

    # Detect AJAX POST for creating a new message
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            new_msg = form.save(commit=False)
            new_msg.user = user
            new_msg.save()

            if request.is_ajax():
                return JsonResponse({'success': True})
            else:
                messages.success(request, "Message sent successfully!")
                return redirect('profile')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
            else:
                messages.error(request, "Please fix the errors below.")

    # Handle other actions: edit, delete, normal GET
    action = request.GET.get('action')
    msg_id = request.GET.get('msg_id')

    form = None
    delete_message = None

    if action == 'edit' and msg_id:
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
        delete_message = get_object_or_404(ContactMessage, pk=msg_id, user=user)
        if request.method == 'POST':
            delete_message.delete()
            messages.success(request, "Message deleted successfully!")
            return redirect('profile')

    else:
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
        'invoices': invoices,
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

                # Only update if not already paid (idempotent)
                if booking.payment_status != 'paid':
                    booking.status = "active"
                    booking.payment_status = 'paid'
                    booking.payment_reference = session.get('payment_intent')

                    # Create invoice if it doesn’t exist
                    if not booking.invoice:
                        invoice = Invoice.objects.create(
                            user=booking.primary_driver,
                            amount=booking.total_price,
                            paid=True,
                            issued_date=now().date()
                        )
                        booking.invoice = invoice

                    booking.save()

            except Booking.DoesNotExist:
                return HttpResponseBadRequest("Booking not found")

    return HttpResponse(status=200)


def retry_payment(request, booking_number):
    booking = get_object_or_404(Booking, booking_number=booking_number)

    # Only allow retry if payment is not completed
    if booking.payment_status == 'completed':
        # redirect to some info page
        return redirect('payment_already_done')

    # Otherwise, redirect to a fresh payment page
    return redirect('payment_page', booking_number=booking.booking_number)

def payment_cancel(request):
    booking_number = request.GET.get('booking_number')
    booking = None
    if booking_number:
        booking = get_object_or_404(Booking, booking_number=booking_number)
    return render(request, 'accounts/cancel.html', {'booking': booking})
