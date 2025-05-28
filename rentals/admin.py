from django.contrib import admin
from .models import (Campervan,
                     Booking,
                     SeasonalRate,
                     CampervanImage,
                     AdditionalService,
                     Invoice)
from django_summernote.admin import SummernoteModelAdmin


class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_number', 'campervan', 'start_date', 'end_date', 'total_price', 'status', 'payment_status')
    list_filter = ('status', 'payment_status', 'additional_insurance')
    search_fields = ('booking_number', 'primary_driver__username', 'primary_driver_name', 'additional_driver_name')
    readonly_fields = ('booking_number', 'total_price', 'created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('campervan', 'start_date', 'end_date', 'total_price', 'status', 'booking_number')
        }),
        ('Primary Driver Details', {
            'fields': ('primary_driver', 'primary_driver_name', 'primary_driver_address_manual'),
        }),
        ('Additional Driver Details', {
            'fields': (
                'additional_driver_name', 'additional_driver_address', 'additional_driver_contact_number',
                'additional_driver_license_number', 'additional_driver_license_expiry', 'additional_driver_license_document',
                'additional_driver_has_license', 'additional_driver_over_21',
            ),
        }),
        ('Services & Insurance', {
            'fields': ('additional_insurance', 'additional_services'),
        }),
        ('Pickup and Dropoff', {
            'fields': ('pickup_location', 'pickup_time', 'dropoff_location', 'dropoff_time'),
        }),
        ('Payment & Invoice', {
            'fields': ('payment_status', 'payment_reference', 'invoice'),
        }),
        ('Customer Notes & Cancellation', {
            'fields': ('customer_notes', 'cancellation_reason', 'refund_amount'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    filter_horizontal = ('additional_services',)

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'amount', 'issued_date', 'paid')
    search_fields = ('invoice_number',)


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
