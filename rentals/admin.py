from django.contrib import admin
from .models import Campervan, Booking, SeasonalRate, CampervanImage, AdditionalService
from django_summernote.admin import SummernoteModelAdmin


class BookingAdmin(admin.ModelAdmin):
    list_display = (
        'booking_number',
        'campervan',
        'start_date',
        'end_date',
        'total_price',
        'status',
        'primary_driver',
        'additional_driver_name',
        'additional_driver_contact_number',
        'additional_driver_has_license',
        'additional_driver_over_21',
        'additional_insurance',
        'display_additional_services',
    )
    list_filter = ('campervan', 'start_date', 'status', 'additional_insurance', 'additional_services')
    search_fields = ('booking_number', 'primary_driver__username', 'additional_driver_name')

    fieldsets = (
        (None, {
            'fields': ('booking_number', 'campervan', 'status')
        }),
        ('Booking Dates', {
            'fields': ('start_date', 'end_date', 'total_price')
        }),
        ('Primary Driver', {
            'fields': ('primary_driver',)
        }),
        ('Additional Driver (Optional)', {
            'fields': (
                'additional_driver_name',
                'additional_driver_address',
                'additional_driver_contact_number',
                'additional_driver_has_license',
                'additional_driver_over_21',
            )
        }),
        ('Additional Options', {
            'fields': ('additional_insurance', 'additional_services')
        }),
    )
    readonly_fields = ('booking_number', 'total_price')

    def display_additional_services(self, obj):
        return ", ".join(service.name for service in obj.additional_services.all())
    display_additional_services.short_description = "Additional Services"

class SeasonalRateAdmin(admin.ModelAdmin):
    list_display = ('start', 'end', 'rate')
    list_filter = ('start',)


class CampervanImageInline(admin.TabularInline):
    model = CampervanImage
    extra = 3


class CampervanAdmin(SummernoteModelAdmin):
    inlines = [CampervanImageInline]
    summernote_fields = ('description',)


@admin.register(AdditionalService)
class AdditionalServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')


admin.site.register(Campervan, CampervanAdmin)
admin.site.register(Booking, BookingAdmin)
admin.site.register(SeasonalRate, SeasonalRateAdmin)
admin.site.register(CampervanImage)
