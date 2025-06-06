from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    receive_offers = models.BooleanField(default=False)
    wants_to_list_camper = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class ContactMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contact_messages')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"


class DiscountCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    percentage = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text="Percentage discount to apply, e.g., 10 for 10%"
    )
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)

    def is_valid(self):
        now = timezone.now()
        if not self.active:
            return False
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_to and now > self.valid_to:
            return False
        return True

    def apply_discount(self, price):
        if not self.is_valid():
            return price
        discount_amount = price * (self.percentage / 100)
        return max(price - discount_amount, 0)

    def __str__(self):
        return self.code
