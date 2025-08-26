from decimal import Decimal
import json
import stripe
from datetime import datetime, timedelta, date
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import get_template
from xhtml2pdf import pisa
import base64
from django.core.files.base import ContentFile
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from .forms import BookingForm, HandoverChecklistForm, HandoverPhotoFormSet, BlockedDateForm
from django.forms import modelformset_factory
from .models import Campervan, Booking, SeasonalRate, HandoverPhoto
from pages.models import CampingDestination
from django.http import JsonResponse
from .models import AdditionalService, Booking, HandoverChecklist, BlockedDate
from .forms import HandoverChecklistForm
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext as _


stripe.api_key = settings.STRIPE_SECRET_KEY

def booking_page(request, pk):
    campervan = get_object_or_404(Campervan, pk=pk)

    date_prices = get_date_price_map(years_ahead=5)
    print("date_prices dict:", date_prices)

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
                    key = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
                    rate = date_prices.get(key, 0)
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
        'date_prices': json.dumps(date_prices),
        'additional_service_prices_json': json.dumps(additional_service_prices),
        'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY,
        'total_price': total_price,
        'subtotal': subtotal,
    })

def booking_form(request):
    return render(request, "rentals/booking_form.html")

def home(request):
    van = Campervan.objects.first()
    bookings = Booking.objects.filter(campervan=van)
    seasonal_rates = SeasonalRate.objects.all()

    booked_dates = [
        {'start': booking.start_date.isoformat(), 'end': booking.end_date.isoformat()}
        for booking in bookings
    ]

    calendar_events = []

    # Booked dates
    for bd in booked_dates:
        calendar_events.append({
            'start': bd['start'],
            'end': bd['end'],
            'title': _('Booked'),
            'display': 'background',
            'backgroundColor': '#f8d7da',
            'borderColor': '#dc3545',
        })

    # Seasonal rates for current + 5 years
    today = date.today()
    years_ahead = 5
    for year_offset in range(years_ahead + 1):
        year = today.year + year_offset
        for season in seasonal_rates:
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

    date_prices = get_date_price_map(years_ahead=5)
    images = van.images.all() if van else []

    return render(request, 'home.html', {
        'van': van,
        'booked_dates': json.dumps(booked_dates),
        'calendar_events': json.dumps(calendar_events),
        'date_prices': json.dumps(date_prices),
        'images': images,
    })


def get_date_price_map(years_ahead=2):
    date_prices = {}
    today = date.today()
    current_year = today.year

    for rate in SeasonalRate.objects.all():
        for year_offset in range(years_ahead + 1):
            year = current_year + year_offset
            try:
                start_date = date(year, rate.start_month, rate.start_day)
                end_date = date(year, rate.end_month, rate.end_day)
                # Handle cross-year seasons
                if end_date < start_date:
                    end_date = date(year + 1, rate.end_month, rate.end_day)

                current = start_date
                while current <= end_date:
                    date_prices[current.strftime('%Y-%m-%d')] = float(rate.rate)
                    current += timedelta(days=1)
                    print(f"Processed rate {rate.pk}: {start_date} - {end_date} -> {rate.rate}")
            except Exception as e:
                print(f"Error processing rate {rate.pk}: {e}")
                continue

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

@csrf_exempt
@login_required(login_url='/account/login/')
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

    start_date = form.cleaned_data['start_date']
    end_date = form.cleaned_data['end_date']

    # Check for overlapping bookings
    existing_booking = Booking.objects.filter(
        campervan=campervan,
        primary_driver=request.user,
        status='active',
        start_date__lte=end_date,
        end_date__gte=start_date
    ).first()

    if existing_booking:
        # Return existing booking session if it exists
        try:
            success_url = "{}?session_id={{CHECKOUT_SESSION_ID}}&booking={}".format(
                request.build_absolute_uri('/accounts/payment-success/'),
                existing_booking.booking_number
            )
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[],
                mode='payment',
                success_url=success_url,
                cancel_url=request.build_absolute_uri('/rentals/booking_form/'),
                metadata={'booking_number': existing_booking.booking_number}
            )
            return JsonResponse({'session_id': checkout_session.id})
        except Exception as e:
            return JsonResponse({'error': f'Error creating Stripe session: {str(e)}'}, status=500)

    # Create new booking object but do NOT mark active yet
    booking = form.save(commit=False)
    booking.campervan = campervan
    booking.primary_driver = request.user
    booking.payment_status = 'pending'
    booking.save()
    form.save_m2m()

    deposit = Decimal('1000.00')
    subtotal = sum(Decimal(service.price) for service in booking.additional_services.all())

    # Calculate taxable subtotal from daily rates
    taxable_subtotal = Decimal('0.00')
    days = (end_date - start_date).days + 1
    for i in range(days):
        rate = campervan.get_rate_for_date(start_date + timedelta(days=i))
        taxable_subtotal += Decimal(rate)

    deposit = Decimal('1000.00')

    total_price = taxable_subtotal + subtotal + deposit

    booking.total_price = total_price
    booking.save()
    form.save_m2m()

    # Create Stripe session
    try:
        success_url = "{}?session_id={{CHECKOUT_SESSION_ID}}&booking={}".format(
            request.build_absolute_uri('/accounts/payment-success/'),
            booking.booking_number
        )

        line_items = [
            {
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': f'Booking {booking.booking_number} - {campervan.name}',
                    },
                    'unit_amount': int(taxable_subtotal * 100 + subtotal * 100),
                },
                'quantity': 1,
                'tax_rates': [settings.STRIPE_MWST_TAX_RATE_ID],
            },
            {
                'price_data': {
                    'currency': 'eur',
                    'product_data': {'name': 'Kaution (Deposit)'},
                    'unit_amount': int(deposit * 100),
                },
                'quantity': 1,
            }
        ]

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=success_url,
            cancel_url=request.build_absolute_uri('/accounts/payment-cancel/'),
            metadata={'booking_number': booking.booking_number}
        )

        # Only mark booking as active after Stripe session creation succeeds
        booking.status = 'pending'
        booking.save()

        return JsonResponse({'session_id': checkout_session.id})

    except Exception as e:
        return JsonResponse({'error': f'Error creating Stripe session: {str(e)}'}, status=500)


@login_required
def retry_payment(request, booking_number):
    try:
        booking = Booking.objects.get(booking_number=booking_number, primary_driver=request.user)
    except Booking.DoesNotExist:
        messages.error(request, "Booking not found.")
        return redirect('home')

    if booking.payment_status == 'paid':
        messages.info(request, "Booking is already paid.")
        return redirect('booking_detail', pk=booking.pk)  # Or some page

    # Create a new Stripe session
    try:
        base_url = request.build_absolute_uri('/accounts/payment-success/')
        success_url = f"{base_url}?session_id={{CHECKOUT_SESSION_ID}}&booking={booking.booking_number}"

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': f'Booking {booking.booking_number} - {booking.campervan.name}',
                    },
                    'unit_amount': int(booking.total_price * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=request.build_absolute_uri('/accounts/payment-cancel/'),
            metadata={'booking_number': booking.booking_number}
        )
        return redirect(checkout_session.url)
    except Exception as e:
        messages.error(request, f"Error creating payment session: {str(e)}")
        return redirect('booking_edit', pk=booking.pk)


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
            booking.status = 'active'
            booking.payment_reference = session.payment_intent
            booking.save()

            # Trigger email
            send_payment_success_email(booking.primary_driver, booking)

            messages.success(request, "Payment successful! Your booking is confirmed.")
            return render(request, 'accounts/success.html', {'booking_number': booking.booking_number})
        except Booking.DoesNotExist:
            messages.error(request, "Booking not found.")
            return redirect('home')
    else:
        messages.error(request, "Payment not successful.")
        return redirect('home')


def payment_cancel(request):
    messages.warning(request, "Payment cancelled.")
    booking_number = request.GET.get('booking')
    booking = None
    if booking_number:
        try:
            from rentals.models import Booking
            booking = Booking.objects.get(booking_number=booking_number)
        except Booking.DoesNotExist:
            booking = None

    return render(request, 'accounts/cancel.html', {
        'booking': booking
    })


def booked_dates_api(request):
    # Fetch all normal bookings
    bookings = Booking.objects.all()
    # Fetch all manually blocked dates
    blocked_dates = BlockedDate.objects.all()

    dates = []

    # Add booked dates
    for booking in bookings:
        current = booking.start_date
        while current <= booking.end_date:
            dates.append(current.isoformat())
            current += timedelta(days=1)

    # Add manually blocked dates
    for block in blocked_dates:
        current = block.start_date
        while current <= block.end_date:
            dates.append({'date': current.isoformat(), 'note': block.note or 'Blocked'})
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


def send_payment_success_email(user, booking):
    # Debug print to check booking details
    print("Booking campervan:", booking.campervan.name)
    print("Booking number:", booking.booking_number)
    print("Booking start date:", booking.start_date)

    name = user.get_full_name() or user.username
    from_email = settings.DEFAULT_FROM_EMAIL

     # User email
    user_subject = _("Your Payment Was Successful")
    user_context = {
        'user': user,
        'name': name,
        'booking': booking,
        'deposit_amount': Decimal('1000.00'),
    }
    user_html = render_to_string("emails/payment_success.html", user_context)
    user_plain = render_to_string("emails/payment_success.txt", user_context)
    send_mail(
        user_subject,
        user_plain,
        from_email,
        [user.email],
        html_message=user_html
    )

    # Admin email
    admin_subject = f"New Booking Received - {booking.booking_number}"

    admin_context = {
        'user': user,
        'booking': booking,
        'total_price': booking.total_price,
        'payment_reference': booking.payment_reference,
        'admin_booking_url': 'http://www.callidercamper.de/admin',
    }
    admin_html = render_to_string("emails/admin_booking_notification.html", admin_context)
    admin_plain = render_to_string("emails/admin_booking_notification.txt", admin_context)
    send_mail(
        admin_subject,
        admin_plain,
        from_email,
        [settings.BOOKING_NOTIFICATION_EMAIL],
        html_message=admin_html
    )


def create_handover_checklist(request):
    if request.method == 'POST':
        form = HandoverChecklistForm(request.POST,  request.FILES)
        formset = HandoverPhotoFormSet(request.POST, request.FILES, queryset=HandoverPhoto.objects.none())

        if form.is_valid() and formset.is_valid():
            checklist = form.save()
            for photo_form in formset:
                if photo_form.cleaned_data and photo_form.cleaned_data.get('image'):
                    photo = photo_form.save(commit=False)
                    photo.checklist = checklist
                    photo.save()
            return redirect('some-success-url')
    else:
        form = HandoverChecklistForm()
        formset = HandoverPhotoFormSet(queryset=HandoverPhoto.objects.none())

    return render(request, 'admin/handoverchecklist.html', {
        'form': form,
        'formset': formset,
        'checklist': checklist,
    })


@staff_member_required
def booking_list(request):
    bookings = Booking.objects.all()
    blocked_dates = BlockedDate.objects.all()

    if request.method == "POST":
        form = BlockedDateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('booking_list')
    else:
        form = BlockedDateForm()

    context = {
        'bookings': bookings,
        'blocked_dates': blocked_dates,
        'blocked_date_form': form,
    }
    return render(request, 'admin_panel/booking_list.html', context)


@staff_member_required
def admin_dashboard(request):
    bookings = Booking.objects.all()
    blocked_dates = BlockedDate.objects.all().order_by('-created_at')

    booking_data = []
    for booking in bookings:
        pickup = booking.handover_checklists.filter(checklist_type='pickup').first()
        return_cl = booking.handover_checklists.filter(checklist_type='return').first()
        booking_data.append({
            'booking': booking,
            'pickup_checklist': pickup,
            'return_checklist': return_cl,
        })

    context = {
        'total_bookings': bookings.count(),
        'booking_data': booking_data,
        'blocked_dates': blocked_dates,
    }
    return render(request, 'admin/admin_dashboard.html', context)

@staff_member_required
def booking_edit(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    handover_checklist = HandoverChecklist.objects.filter(booking=booking, checklist_type='pickup').first()
    return_checklist = HandoverChecklist.objects.filter(booking=booking, checklist_type='return').first()

    handover_photos = handover_checklist.handoverphoto_set.all() if handover_checklist else []

    if request.method == 'POST':
        form = BookingForm(request.POST, instance=booking)
        if form.is_valid():
            form.save()
            return redirect('booking_list')
    else:
        form = BookingForm(instance=booking)

    # ✅ Define context explicitly
    context = {
        'booking': booking,
        'form': form,
        'handover_checklist': handover_checklist,
        'return_checklist': return_checklist,
        'handover_photos': handover_photos,
    }

    return render(request, 'rentals/booking_edit_admin.html', context)

@staff_member_required
def booking_delete(request, pk):
    booking = get_object_or_404(Booking, pk=pk)
    if request.method == 'POST':
        booking.delete()
        return redirect('booking_list')
    return render(request, 'admin_panel/booking_confirm_delete.html', {'booking': booking})

@staff_member_required
def handover_checklist(request, booking_number):
    booking = get_object_or_404(Booking, booking_number=booking_number)
    handover_checklist = booking.handover_checklists.filter(checklist_type='pickup').first()

    if request.method == 'POST':
        form = HandoverChecklistForm(request.POST, instance=handover_checklist)
        if form.is_valid():
            checklist = form.save(commit=False)
            checklist.booking = booking
            checklist.checklist_type = 'pickup'

            # ✅ Handle base64 signature data
            signature_data = request.POST.get('signature_data')
            if signature_data:
                format, imgstr = signature_data.split(';base64,')
                ext = format.split('/')[-1]  # png or jpeg
                filename = f"signature_{booking.booking_number}.{ext}"
                checklist.customer_signature = ContentFile(base64.b64decode(imgstr), name=filename)

            checklist.save()
            return redirect('booking_edit', pk=booking.pk)
    else:
        form = HandoverChecklistForm(instance=handover_checklist)

    handover_photos = handover_checklist.handoverphoto_set.all() if handover_checklist else []

    return render(request, 'admin/handoverchecklist.html', {
        'form': form,
        'booking': booking,
        'handover_checklist': handover_checklist,
        'handover_photos': handover_photos,
    })


@staff_member_required
def return_checklist(request, booking_number):
    booking = get_object_or_404(Booking, booking_number=booking_number)

    # Try to get an existing return checklist
    checklist = booking.handover_checklists.filter(checklist_type='return').first()
    handover = booking.handover_checklists.filter(checklist_type='pickup').first()

    if request.method == 'POST':
        form = HandoverChecklistForm(request.POST, request.FILES, instance=checklist)
        if form.is_valid():
            return_checklist = form.save(commit=False)
            return_checklist.booking = booking
            return_checklist.checklist_type = 'return'

            # Handle signature
            signature_data = request.POST.get('signature_data')
            if signature_data:
                format, imgstr = signature_data.split(';base64,')
                ext = format.split('/')[-1]
                filename = f"return_signature_{booking.booking_number}.{ext}"
                return_checklist.customer_signature = ContentFile(
                    base64.b64decode(imgstr),
                    name=filename
                )

            return_checklist.save()
            form.save_m2m()

            # ✅ Update booking status to closed
            booking.status = 'closed'
            booking.save()

            # ✅ Send thank-you email in German
            send_mail(
                subject="Vielen Dank für Ihre Buchung bei Calli!",
                message=(
                    f"Liebe/r {booking.primary_driver.get_full_name() or booking.primary_driver.username},\n\n"
                    "Vielen Dank, dass Sie bei Calli dem Camper gebucht haben! Wir hoffen, Sie hatten einen schönen Urlaub.\n"
                    "Bis zum nächsten Mal! Sollten Sie Probleme oder Anregungen haben, "
                    "können Sie uns jederzeit unter abenteuer@callidercamper.de kontaktieren."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[booking.primary_driver.email],
                fail_silently=False,
            )

            return redirect('booking_edit', pk=booking.pk)
    else:
        if checklist:
            form = HandoverChecklistForm(instance=checklist)
        elif handover:
            initial_data = {
                'driver_name': handover.driver_name,
                'windshields': handover.windshields,
                'paintwork': handover.paintwork,
                'bodywork': handover.bodywork,
                'tires_front': handover.tires_front,
                'tires_rear': handover.tires_rear,
                'seats': handover.seats,
                'upholstery': handover.upholstery,
                'windows': handover.windows,
                'lights': handover.lights,
                'flooring': handover.flooring,
                'known_damage': handover.known_damage,
            }
            form = HandoverChecklistForm(initial=initial_data)
        else:
            form = HandoverChecklistForm()

    return render(request, 'admin/returnchecklist.html', {
        'form': form,
        'booking': booking,
    })

def checklist_detail(request, pk):
    checklist = get_object_or_404(HandoverChecklist, pk=pk)
    return render(request, 'checklists/checklist_details.html', {'checklist': checklist})

def checklist_pdf(request, pk):
    checklist = get_object_or_404(HandoverChecklist, pk=pk)
    template_path = 'checklists/checklist_pdf.html'
    context = {'checklist': checklist}

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'filename=checklist_{checklist.booking.booking_number}.pdf'
        )

    template = get_template(template_path)
    html = template.render(context)

    # Create PDF
    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse(
            'We had some errors with PDF generation <pre>'
            + html + '</pre>')
    return response


def handover_photo_upload(request):
    if request.method == 'POST':
        formset = HandoverPhotoFormSet(   # pylint: disable=no-member
            request.POST, request.FILES,
            queryset=HandoverPhoto.objects.none()   # pylint: disable=no-member
            )
        if formset.is_valid():
            formset.save()
            return redirect('success-url')
    else:
        formset = HandoverPhotoFormSet(
            queryset=HandoverPhoto.objects.none()  # pylint: disable=no-member
            )

    return render(request, 'upload.html', {'formset': formset})


@staff_member_required
def save_checklist(request, pk):
    checklist = get_object_or_404(HandoverChecklist, pk=pk)

    if request.method == 'POST':
        form = HandoverChecklistForm(request.POST, request.FILES, instance=checklist)
        if form.is_valid():
            checklist = form.save(commit=False)

            # ✅ Handle base64 signature
            signature_data = request.POST.get('signature_data')
            if signature_data:
                format, imgstr = signature_data.split(';base64,')
                ext = format.split('/')[-1]  # usually 'png'
                filename = f"signature_{checklist.booking.booking_number}.{ext}"
                checklist.customer_signature = ContentFile(base64.b64decode(imgstr), name=filename)

            checklist.save()
            form.save_m2m()
            messages.success(request, "Checklist updated with signature.")
            return redirect('checklist_detail', pk=pk)
    else:
        form = HandoverChecklistForm(instance=checklist)

    return render(request, 'checklists/checklist_details.html', {
        'checklist': checklist,
        'form': form,
    })

@staff_member_required
def blocked_date_add(request):
    if request.method == 'POST':
        form = BlockedDateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = BlockedDateForm()
    return render(request, 'admin/blocked_date_form.html', {'form': form})

@staff_member_required
def blocked_date_edit(request, pk):
    bd = get_object_or_404(BlockedDate, pk=pk)
    if request.method == 'POST':
        form = BlockedDateForm(request.POST, instance=bd)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')
    else:
        form = BlockedDateForm(instance=bd)
    return render(request, 'admin/blocked_date_form.html', {'form': form})

@staff_member_required
def blocked_date_delete(request, pk):
    bd = get_object_or_404(BlockedDate, pk=pk)
    if request.method == 'POST':
        bd.delete()
        return redirect('admin_dashboard')
    return render(request, 'admin/blocked_date_confirm_delete.html', {'blocked_date': bd})
