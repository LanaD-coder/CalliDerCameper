from django.contrib import admin, messages
from decimal import Decimal
from django import forms
from .models import (
    Campervan,
    Booking,
    SeasonalRate,
    CampervanImage,
    AdditionalService,
    Invoice,
)
from django_summernote.admin import SummernoteModelAdmin


class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_number', 'campervan', 'start_date', 'end_date', 'total_price', 'status', 'payment_status')
    list_filter = ('status', 'payment_status')
    search_fields = ('booking_number', 'primary_driver_name', 'additional_driver_name')
    readonly_fields = ('booking_number', 'total_price', 'created_at', 'updated_at', 'deposit_amount_display')
    ordering = ('-created_at',)
    filter_horizontal = ('additional_services',)

    fieldsets = (
        (None, {
            'fields': ('campervan', 'start_date', 'end_date', 'total_price', 'status', 'booking_number')
        }),
        ('Primary Driver Details', {
            'fields': (
                'primary_driver_name', 'primary_driver_street_name', 'primary_driver_street_number',
                'primary_driver_postal_code', 'primary_driver_town', 'primary_driver_country'
            ),
        }),
        ('Additional Driver (Optional)', {
            'fields': (
                'additional_driver_name', 'additional_driver_email',
                'additional_driver_contact_number', 'additional_driver_street', 'additional_driver_postal_code',
                'additional_driver_town', 'additional_driver_country',
            ),
        }),
        ('Discount and Deposit', {
            'fields': ('discount_code', 'deposit_amount_display'),
        }),
        ('Services', {
            'fields': ('additional_services',),
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


    def deposit_amount_display(self, obj):
        deposit_value = getattr(obj, 'deposit', Decimal('1000.00'))
        return f"€{deposit_value:,.2f}"

    deposit_amount_display.short_description = "Deposit"

    def save_model(self, request, obj, form, change):
        # Warn if both FK and manual name are filled
        if obj.primary_driver and obj.primary_driver_name:
            messages.warning(
                request,
                "Both 'primary_driver' and 'primary_driver_name' are set. "
                "Only one should be used. Consider clearing one."
            )
        super().save_model(request, obj, form, change)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'amount', 'issued_date', 'paid')
    search_fields = ('invoice_number',)


class SeasonalRateForm(forms.ModelForm):
    start_date = forms.DateField(required=False, label="Start Date (for UI only)")
    end_date = forms.DateField(required=False, label="End Date (for UI only)")

    class Meta:
        model = SeasonalRate
        fields = ['start_month', 'start_day', 'end_month', 'end_day', 'rate']

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date:
            cleaned_data["start_month"] = start_date.month
            cleaned_data["start_day"] = start_date.day
        if end_date:
            cleaned_data["end_month"] = end_date.month
            cleaned_data["end_day"] = end_date.day

        return cleaned_data


class SeasonalRateAdmin(admin.ModelAdmin):
    form = SeasonalRateForm
    list_display = ('start_month', 'start_day', 'end_month', 'end_day', 'rate')
    list_filter = ('start_month', 'end_month', 'rate')


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
