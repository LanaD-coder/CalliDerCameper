import uuid
from django.db import models
import random
import string
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField


class Campervan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    available = models.BooleanField(default=True)

    def get_rate_for_date(self, date):
        rates = SeasonalRate.objects.all()
        for rate in rates:
            if rate.includes_date(date):
                return rate.rate
        return None

    def __str__(self):
        return self.name


class CampervanImage(models.Model):
    campervan = models.ForeignKey(Campervan, related_name='images', on_delete=models.CASCADE)
    image = CloudinaryField('image')

    def __str__(self):
        return f"Image for {self.campervan.name}"


class AdditionalService(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Invoice(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices', null=True)
    invoice_number = models.CharField(max_length=36, unique=True, editable=False, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issued_date = models.DateField(auto_now_add=True)
    paid = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {'Paid' if self.paid else 'Unpaid'}"


class Booking(models.Model):
    campervan = models.ForeignKey(Campervan, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField()
    end_date = models.DateField()
    deposit_amount = models.DecimalField(max_digits=8, decimal_places=2, default=1000.00)
    additional_services = models.ManyToManyField(AdditionalService, blank=True)
    total_price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    primary_driver = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='primary_bookings'
    )

    @property
    def primary_driver_phone(self):
        if self.primary_driver and hasattr(self.primary_driver, 'userprofile'):
            return self.primary_driver.userprofile.phone_number
        return None

    @property
    def primary_driver_address(self):
        if self.primary_driver and hasattr(self.primary_driver, 'userprofile'):
            return self.primary_driver.userprofile.address
        return None

    discount_code = models.CharField(max_length=50, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2, default=0)

    # New editable primary driver fields if you want to allow manual input instead of FK
    primary_driver_name = models.CharField(max_length=100, blank=True, null=True)
    primary_driver_street_name = models.CharField(max_length=100, blank=True, null=True)
    primary_driver_street_number = models.CharField(max_length=20, blank=True, null=True)
    primary_driver_postal_code = models.CharField(max_length=20, blank=True, null=True)
    primary_driver_town = models.CharField(max_length=100, blank=True, null=True)
    primary_driver_country = models.CharField(max_length=100, blank=True, null=True)

    # Additional driver info (optional)
    additional_driver_name = models.CharField(max_length=100, blank=True, null=True)
    additional_driver_street = models.CharField(max_length=255, blank=True, null=True)
    additional_driver_postal_code = models.CharField(max_length=20, blank=True, null=True)
    additional_driver_town = models.CharField(max_length=100, blank=True, null=True)
    additional_driver_country = models.CharField(max_length=100, blank=True, null=True)
    additional_driver_email = models.EmailField(blank=True, null=True)
    additional_driver_contact_number = models.CharField(max_length=20, blank=True, null=True)

    # Confirmations as BooleanFields
    additional_driver_has_license = models.BooleanField(default=False)
    additional_driver_over_21 = models.BooleanField(default=False)

    deposit_paid = models.BooleanField(default=True)
    deposit_hidden = models.BooleanField(default=False)

    # Pickup and dropoff details
    pickup_location = models.CharField(max_length=255, blank=True, null=True)
    pickup_time = models.TimeField(blank=True, null=True)
    dropoff_location = models.CharField(max_length=255, blank=True, null=True)
    dropoff_time = models.TimeField(blank=True, null=True)

    # Customer notes or special requests
    customer_notes = models.TextField(blank=True, null=True)
    customer_signature = models.ImageField(
        upload_to='signatures/', blank=True, null=True, verbose_name='Customer Signature'
    )

    # Payment info/status
    payment_status_choices = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    payment_status = models.CharField(max_length=10, choices=payment_status_choices, default='pending')
    payment_reference = models.CharField(max_length=100, blank=True, null=True)

    # Invoice relation
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, blank=True, null=True, related_name='bookings')

    booking_number = models.CharField(max_length=12, unique=True, editable=False, blank=True)

    @staticmethod
    def generate_booking_number(prefix='cdc25', number_length=5):
        last_booking = Booking.objects.filter(booking_number__startswith=prefix).order_by('-booking_number').first()
        if last_booking and last_booking.booking_number:
            last_number = int(last_booking.booking_number.replace(prefix, ''))
            new_number = last_number + 1
        else:
            new_number = 1
        return f"{prefix}{str(new_number).zfill(number_length)}"

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    # Cancellation/refund details
    cancellation_reason = models.TextField(blank=True, null=True)
    refund_amount = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    # Checklists
    pickup_checklist = models.OneToOneField(
        'HandoverChecklist',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pickup_booking'
    )
    return_checklist = models.OneToOneField(
        'HandoverChecklist',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='return_booking'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # Date validation
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError("End date cannot be before start date.")

            # Overlapping bookings check
            overlapping = Booking.objects.filter(
                campervan=self.campervan,
                end_date__gte=self.start_date,
                start_date__lte=self.end_date
            ).exclude(pk=self.pk)

            if overlapping.exists():
                raise ValidationError("This campervan is already booked for the selected dates.")

    def cancel(self, reason=None, refund_amount=None):
        """Cancel the booking with optional reason and refund"""
        self.status = 'cancelled'
        if reason:
            self.cancellation_reason = reason
        if refund_amount:
            self.refund_amount = refund_amount
            self.payment_status = 'refunded'
        self.save()

    def save(self, *args, **kwargs):
        self.clean()

        if not self.start_date or not self.end_date:
            raise ValidationError("Start date and end date must be set before saving a booking.")

        if not self.booking_number:
            self.booking_number = Booking.generate_booking_number()

        # Price calculation
        days = (self.end_date - self.start_date).days + 1
        total = 0
        for i in range(days):
            current_date = self.start_date + timedelta(days=i)
            rate = self.campervan.get_rate_for_date(current_date)
            if rate is None:
                raise ValidationError(f"No seasonal rate found for date {current_date}")
            total += rate

        # Subtract discount
        total -= self.discount_amount or 0
        if total < 0:
            total = 0

        self.total_price = total

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.booking_number} for {self.campervan.name} ({self.start_date} to {self.end_date})"


class SeasonalRate(models.Model):
    start_month = models.PositiveSmallIntegerField()
    start_day = models.PositiveSmallIntegerField()
    end_month = models.PositiveSmallIntegerField()
    end_day = models.PositiveSmallIntegerField()
    rate = models.DecimalField(max_digits=6, decimal_places=2)

    def includes_date(self, date_to_check):
        check = date_to_check.month * 100 + date_to_check.day
        start = self.start_month * 100 + self.start_day
        end = self.end_month * 100 + self.end_day

        if start <= end:
            return start <= check <= end
        else:
            return check >= start or check <= end

    def __str__(self):
        return f"{self.start_month}/{self.start_day} to {self.end_month}/{self.end_day}: €{self.rate}"


class HandoverChecklist(models.Model):
    TYPE_CHOICES = [
        ('pickup', 'Pickup'),
        ('return', 'Return'),
    ]

    CONDITION_CHOICES = [
        ('good', 'Good'),
        ('damaged', 'Damaged'),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='handover_checklists')
    checklist_type = models.CharField(max_length=10, choices=[('pickup', 'Pickup'), ('return', 'Return')])
    date = models.DateField()
    time = models.TimeField()
    driver_name = models.CharField(max_length=100, blank=True)
    phone_contact = models.CharField(max_length=30, blank=True)
    odometer = models.PositiveIntegerField(null=True, blank=True)
    location = models.TextField(blank=True)

    # Exterior
    windshields = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    paintwork = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    bodywork = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    tires_front = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    tires_rear = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')

    # Interior
    seats = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    upholstery = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    windows = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    lights = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    flooring = models.CharField(max_length=10, choices=CONDITION_CHOICES, default='good')
    known_damage = models.TextField(blank=True)

    notes = models.TextField(blank=True)

    customer_signature = models.ImageField(upload_to='signatures/', blank=True, null=True)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.checklist_type.title()} Checklist - {self.booking.booking_number}"


class HandoverPhoto(models.Model):
    checklist = models.ForeignKey(HandoverChecklist, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='handover_photos/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class BlockedDate(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    note = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date']
        verbose_name = "Dates Booked"
        verbose_name_plural = "Dates Booked"

    def __str__(self):
        return f"{self.start_date} → {self.end_date} ({self.note})"
