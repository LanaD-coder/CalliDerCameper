from django.contrib import admin
from .models import Campervan, Booking, SeasonalRate, CampervanImage
from django_summernote.admin import SummernoteModelAdmin


class BookingAdmin(admin.ModelAdmin):
    list_display = ('campervan', 'start_date', 'end_date', 'total_price')
    list_filter = ('campervan', 'start_date')


class SeasonalRateAdmin(admin.ModelAdmin):
    list_display = ('start', 'end', 'rate')
    list_filter = ('start',)


class CampervanImageInline(admin.TabularInline):
    model = CampervanImage
    extra = 3


class CampervanAdmin(SummernoteModelAdmin):
    inlines = [CampervanImageInline]
    summernote_fields = ('description',)


admin.site.register(Campervan, CampervanAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(SeasonalRate, SeasonalRateAdmin)
admin.site.register(CampervanImage)
