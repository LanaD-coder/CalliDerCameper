from django.contrib import admin
from .models import Campervan, Booking, SeasonalRate

# Register each model
admin.site.register(Campervan)
admin.site.register(Booking)
admin.site.register(SeasonalRate)