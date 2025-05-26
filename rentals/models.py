import uuid
from django.db import models
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField


class Campervan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price_per_day = models.DecimalField(max_digits=6, decimal_places=2)
    available = models.BooleanField(default=True)

    def get_rate_for_date(self, date):
        rate = SeasonalRate.objects.filter(start__lte=date, end__gte=date).first()
        return rate.rate if rate else self.price_per_day

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


class Booking(models.Model):
    campervan = models.ForeignKey(Campervan, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField()
    end_date = models.DateField()
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

    # Additional driver info (optional)
    additional_driver_name = models.CharField(max_length=100, blank=True, null=True)
    additional_driver_address = models.TextField(blank=True, null=True)
    additional_driver_contact_number = models.CharField(max_length=20, blank=True, null=True)

    # Confirmations as BooleanFields
    additional_driver_has_license = models.BooleanField(default=False)
    additional_driver_over_21 = models.BooleanField(default=False)

    # Additional services and insurance
    additional_insurance = models.BooleanField(default=False)
    additional_services = models.ManyToManyField(AdditionalService, blank=True)

    booking_number = models.CharField(max_length=36, unique=True, editable=False, blank=True)

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def clean(self):
        # Date validation
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

    def cancel(self):
        """Cancel the booking"""
        self.status = 'cancelled'
        self.save()

    def save(self, *args, **kwargs):
        self.clean()  # Run validations before save

        if not self.booking_number:
            self.booking_number = str(uuid.uuid4())

        days = (self.end_date - self.start_date).days + 1
        total = 0
        for i in range(days):
            current_date = self.start_date + timedelta(days=i)
            rate = self.campervan.get_rate_for_date(current_date)
            total += rate
        self.total_price = total

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.booking_number} for {self.campervan.name} ({self.start_date} to {self.end_date})"

class SeasonalRate(models.Model):
    start = models.DateField()
    end = models.DateField()
    rate = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.start} to {self.end}: ${self.rate}"
