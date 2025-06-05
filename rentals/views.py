from decimal import Decimal
import json
import stripe
from datetime import datetime, timedelta, date
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from .forms import BookingForm
from .models import Campervan, Booking, SeasonalRate
from pages.models import CampingDestination
from accounts.models import DiscountCode
from django.http import JsonResponse
from .models import AdditionalService
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext as _


def home(request):
    van = Campervan.objects.first()
    bookings = Booking.objects.filter(campervan=van)
    seasonal_rates = SeasonalRate.objects.all()

    booked_dates = [
        {'start': booking.start_date.isoformat(), 'end': booking.end_date.isoformat()}
        for booking in bookings
    ]

    calendar_events = []

    for bd in booked_dates:
        calendar_events.append({
            'start': bd['start'],
            'end': bd['end'],
            'title': _('Booked'),
            'display': 'background',
            'backgroundColor': '#f8d7da',
            'borderColor': '#dc3545',
        })

    for season in seasonal_rates:
        year = 2025
        start_date = date(year, season.start_month, season.start_day)
        end_date = date(year, season.end_month, season.end_day)

        if end_date < start_date:
            end_date = date(year + 1, season.end_month, season.end_day)

        calendar_events.append({
            'start': start_date.isoformat(),
            'end': (end_date + timedelta(days=1)).isoformat(),
            'display': 'background',
            'backgroundColor': '#d1ecf1',
            'borderColor': '#17a2b8',
        })

    date_prices = get_date_price_map()
    destinations = CampingDestination.objects.all()

    return render(request, 'home.html', {
        'van': van,
        'booked_dates': json.dumps(booked_dates),
        'calendar_events': json.dumps(calendar_events),
        'date_prices': json.dumps(date_prices),
        'destinations': destinations,
    })


def get_date_price_map():
    date_prices = {}
    year = 2025

    for rate in SeasonalRate.objects.all():
        start_date = date(year, rate.start_month, rate.start_day)
        end_date = date(year, rate.end_month, rate.end_day)
        if end_date < start_date:
            end_date = date(year + 1, rate.end_month, rate.end_day)

        current = start_date
        while current <= end_date:
            date_prices[current.strftime('%Y-%m-%d')] = float(rate.rate)
            current += timedelta(days=1)

    return date_prices


def campervan_detail(request):
    van = Campervan.objects.first()
    images = van.images.all()

    date_prices_dict = get_date_price_map()

    context = {
        'van': van,
        'van_images': images,
        'date_prices': json.dumps(date_prices_dict),
    }

    return render(request, 'home.html', context)


stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required(login_url='/account/login/')
def booking_page(request, pk):
    campervan = get_object_or_404(Campervan, pk=pk)

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    total_price = None
    subtotal = Decimal('0.00')

    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            if end_date >= start_date:
                days = (end_date - start_date).days + 1
                for i in range(days):
                    rate = campervan.get_rate_for_date(start_date + timedelta(days=i))
                    subtotal += Decimal(rate)
                total_price = subtotal
        except ValueError:
            pass  # Show blank form with no price if dates invalid

    form = BookingForm(
        initial={'start_date': start_date_str, 'end_date': end_date_str},
        user=request.user,
        campervan=campervan
    )

    additional_service_prices = {
        str(service.pk): float(service.price)
        for service in AdditionalService.objects.all()
    }

    return render(request, 'rentals/booking_form.html', {
        'form': form,
        'campervan': campervan,
        'date_prices_json': json.dumps(get_date_price_map()),
        'additional_service_prices_json': json.dumps(additional_service_prices),
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
        'total_price': total_price,
        'subtotal': subtotal,
    })

@csrf_exempt  # or use proper CSRF token with JS if login-protected
def create_booking_ajax(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request'}, status=405)

    campervan = get_object_or_404(Campervan, pk=pk)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'errors': 'Invalid JSON'}, status=400)

    form = BookingForm(data, user=request.user, campervan=campervan)
    form.instance.campervan = campervan

    if not form.is_valid():
        return JsonResponse({'errors': form.errors}, status=400)

    booking = form.save(commit=False)
    booking.campervan = campervan
    booking.primary_driver = request.user
    booking.payment_status = 'pending'
    booking.status = 'active'
    booking.save()
    form.save_m2m()

    discount_code_str = form.cleaned_data.get('discount_code')
    discount_obj = None
    discount_amount = Decimal('0.00')
    deposit = Decimal('1000.00')
    subtotal = Decimal('0.00')

    if discount_code_str:
        try:
            discount_obj = DiscountCode.objects.get(code__iexact=discount_code_str, active=True)
            if not discount_obj.is_valid():
                return JsonResponse({'errors': {'discount_code': ['Invalid or expired code']}}, status=400)
            discount_amount = discount_obj.amount
        except DiscountCode.DoesNotExist:
            return JsonResponse({'errors': {'discount_code': ['Invalid discount code']}}, status=400)

    for service in booking.additional_services.all():
        subtotal += Decimal(service.price)

    days = (booking.end_date - booking.start_date).days + 1
    for i in range(days):
        rate = campervan.get_rate_for_date(booking.start_date + timedelta(days=i))
        subtotal += Decimal(rate)

    # Add deposit always
    subtotal += deposit

    grand_total = max(Decimal('0.00'), subtotal - discount_amount)

    booking.total_price = grand_total
    booking.discount_code = discount_obj
    booking.save()

    if discount_obj:
        discount_obj.used_count += 1
        discount_obj.save()

    try:
        base_url = request.build_absolute_uri('/accounts/payment-success/')
        success_url = f"{base_url}?session_id={{CHECKOUT_SESSION_ID}}&booking={booking.booking_number}"
        print(f"Success URL: {success_url}")

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': f'Booking {booking.booking_number} - {campervan.name}',
                    },
                    'unit_amount': int(grand_total * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=request.build_absolute_uri('/accounts/payment-cancel/'),
            metadata={'booking_number': booking.booking_number}
        )
        return JsonResponse({'session_id': checkout_session.id})
    except Exception as e:
        return JsonResponse({'error': f'Error creating Stripe session: {str(e)}'}, status=500)


def render_booking_form(request, form, campervan):
    return render(request, 'rentals/booking_form.html', {
        'form': form,
        'campervan': campervan,
        'date_prices_json': json.dumps(get_date_price_map()),
        'additional_service_prices_json': json.dumps({
            str(s.pk): float(s.price) for s in AdditionalService.objects.all()
        }),
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
    })


@csrf_exempt
def create_payment_intent(request):
    if request.method == "POST":
        data = json.loads(request.body)
        total_cost_cents = int(data.get("total_cost") * 100)  # amount in cents

        try:
            intent = stripe.PaymentIntent.create(
                amount=total_cost_cents,
                currency="eur",  # or your currency
            )
            return JsonResponse({"client_secret": intent.client_secret})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


def payment_success(request):
    session_id = request.GET.get('session_id')
    booking_number = request.GET.get('booking')

    if not session_id or not booking_number:
        messages.error(request, "Invalid payment confirmation.")
        return redirect('home')

    stripe.api_key = settings.STRIPE_SECRET_KEY
    session = stripe.checkout.Session.retrieve(session_id)

    if session.payment_status == 'paid':
        try:
            booking = Booking.objects.get(booking_number=booking_number)
            booking.payment_status = 'paid'
            booking.payment_reference = session.payment_intent
            booking.status = 'active'
            booking.save()

            # Trigger email
            send_payment_success_email(booking.primary_driver)

            messages.success(request, "Payment successful! Your booking is confirmed.")
            return render(request, 'accounts/success.html', {'booking_number': booking.booking_number})
        except Booking.DoesNotExist:
            messages.error(request, "Booking not found.")
            return redirect('home')
    else:
        messages.error(request, "Payment not successful.")
        return redirect('home')


def send_payment_success_email(user):
    name = user.get_full_name() or user.username
    subject = _("Your Payment Was Successful")
    context = {'user': user, 'name': name}
    html_message = render_to_string("emails/payment_success.html", context)
    plain_message = render_to_string("emails/payment_success.txt", context)
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]

    send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)


def payment_cancel(request):
    messages.warning(request, "Payment cancelled.")
    return render(request, 'accounts/cancel.html')


def booked_dates_api(request):
    bookings = Booking.objects.all()
    dates = []
    for booking in bookings:
        current = booking.start_date
        while current <= booking.end_date:
            dates.append(current.isoformat())
            current += timedelta(days=1)
    return JsonResponse({'booked_dates': dates})


@csrf_exempt
def check_availability(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            start = datetime.strptime(data['start_date'], "%Y-%m-%d").date()
            end = datetime.strptime(data['end_date'], "%Y-%m-%d").date()

            overlapping = Booking.objects.filter(start_date__lte=end, end_date__gte=start).exists()
            if overlapping:
                return JsonResponse({"available": False, "errors": ["The car is not available for the selected dates."]})
            return JsonResponse({"available": True})
        except Exception as e:
            return JsonResponse({"available": False, "errors": [str(e)]})
