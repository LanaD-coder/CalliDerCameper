from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import HandoverChecklist

@receiver(post_save, sender=HandoverChecklist)
def update_booking_status_on_return_checklist(sender, instance, created, **kwargs):
    if instance.checklist_type == 'return' and instance.completed:
        booking = instance.booking
        if booking.status != 'completed':
            booking.status = 'completed'
            booking.save()
