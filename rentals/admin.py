from django.contrib import admin
from .models import Campervan, Booking, SeasonalRate


class BookingAdmin(admin.ModelAdmin):
    list_display = ('campervan', 'start_date', 'end_date', 'total_price')
    list_filter = ('campervan', 'start_date')


class SeasonalRateAdmin(admin.ModelAdmin):
    list_display = ('start', 'end', 'rate')
    list_filter = ('start',)



# Register each model
admin.site.register(Campervan)
admin.site.register(Booking)
admin.site.register(SeasonalRate)