from django.db import models
from datetime import timedelta


class Campervan(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price_per_day = models.DecimalField(max_digits=6, decimal_places=2)
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Booking(models.Model):
    campervan = models.ForeignKey(Campervan, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)

    def save(self, *args, **kwargs):
        days = (self.end_date - self.start_date).days + 1
        total = 0

        for i in range(days):
            current_date = self.start_date + timedelta(days=i)
            rate = get_rate_for_date(current_date)
            total += rate

        self.total_price = total
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking from {self.start_date} to {self.end_date}"


class SeasonalRate(models.Model):
    start = models.DateField()
    end = models.DateField()
    rate = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"{self.start} to {self.end}: ${self.rate}"


def get_rate_for_date(date, default_rate=120.00):
    rate = SeasonalRate.objects.filter(start__lte=date, end__gte=date).first()
    return rate.rate if rate else default_rate