from django.contrib import admin
from .models import Campervan, Booking, SeasonalRate, CampervanImage


class BookingAdmin(admin.ModelAdmin):
    list_display = ('campervan', 'start_date', 'end_date', 'total_price')
    list_filter = ('campervan', 'start_date')


class SeasonalRateAdmin(admin.ModelAdmin):
    list_display = ('start', 'end', 'rate')
    list_filter = ('start',)


class CampervanImageInline(admin.TabularInline):
    model = CampervanImage
    extra = 3


class CampervanAdmin(admin.ModelAdmin):
    inlines = [CampervanImageInline]

# Register each model
admin.site.register(Campervan)
admin.site.register(Booking)
admin.site.register(SeasonalRate)
admin.site.register(CampervanImage)