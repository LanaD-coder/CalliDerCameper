from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    receive_offers = models.BooleanField(default=False)
    wants_to_list_camper = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username