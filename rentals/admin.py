from django.contrib import admin, messages
import base64, uuid
from django.core.files.base import ContentFile
from django.utils.safestring import mark_safe
from decimal import Decimal
from django import forms
from .models import (
    Campervan,
    Booking,
    SeasonalRate,
    CampervanImage,
    AdditionalService,
    Invoice,
    HandoverPhoto,
    HandoverChecklist
)
from .forms import ReturnChecklistForm, HandoverChecklistForm, BookingAdminForm
from django_summernote.admin import SummernoteModelAdmin


class HandoverPhotoInline(admin.TabularInline):
    model = HandoverPhoto
    extra = 1

class HandoverChecklistInline(admin.StackedInline):
    model = HandoverChecklist
    extra = 1
    inlines = [HandoverPhotoInline]

class HandoverChecklistAdmin(admin.ModelAdmin):
    form = HandoverChecklistForm
    readonly_fields = ('signature_canvas',)

    fieldsets = (
        (None, {
            'fields': ('checklist_type', 'date', 'time', 'driver_name', 'phone_contact', 'odometer', 'location'),
        }),
        ('Exterior Check', {
            'fields': ('windshields', 'paintwork', 'bodywork', 'tires_front', 'tires_rear'),
        }),
        ('Interior Check', {
            'fields': ('seats', 'upholstery', 'windows', 'lights', 'flooring', 'known_damage', 'notes'),
        }),
        ('Customer Signature', {
            'fields': ('signature_canvas',),
        }),
    )

    class Media:
        js = (
            'https://cdn.jsdelivr.net/npm/signature_pad@4.0.0/dist/signature_pad.umd.min.js',
            'js/admin_signature.js',
        )

    def signature_canvas(self, obj):
        existing_image_html = ""
        if obj and obj.customer_signature:
            existing_image_html = f"""
                <div style="margin-bottom: 10px;">
                    <strong>Existing Signature:</strong><br>
                    <img src="{obj.customer_signature.url}" alt="Customer Signature" style="border:1px solid #000; max-width:400px; max-height:150px;">
                </div>
            """

        return mark_safe(f"""
            {existing_image_html}
            <label>Draw/Update Signature:</label><br>
            <canvas id="signature-canvas-{obj.pk if obj else 'new'}" width="400" height="150" style="border:1px solid #000;"></canvas><br>
            <button type="button" id="clear-signature">Clear</button>
            <input type="hidden" name="signature_data" id="id_signature_data">
            <script>
                const canvas = document.getElementById("signature-canvas-{obj.pk if obj else 'new'}");
                const signaturePad = new SignaturePad(canvas);
                const hiddenInput = document.getElementById("id_signature_data");

                {f"""
                var img = new Image();
                img.onload = function() {{
                    canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
                }};
                img.src = '{obj.customer_signature.url}';
                """ if obj and obj.customer_signature else ""}

                document.querySelector("form").addEventListener("submit", function() {{
                    if (!signaturePad.isEmpty()) {{
                        hiddenInput.value = signaturePad.toDataURL();
                    }}
                }});

                document.getElementById("clear-signature").addEventListener("click", function() {{
                    signaturePad.clear();
                    hiddenInput.value = "";
                }});
            </script>
        """)


class ReturnChecklistInline(admin.StackedInline):
    model = HandoverChecklist
    form = ReturnChecklistForm
    extra = 0
    readonly_fields = ('initial_odometer_display',)
    exclude = ('checklist_type',)

    def initial_odometer_display(self, obj):
        handover = None
        try:
            booking = obj.booking
            handover = booking.checklists.filter(checklist_type='pickup').first()
        except Exception:
            pass

        if handover:
            return handover.odometer
        return "N/A"

    initial_odometer_display.short_description = "Initial Odometer (from handover)"

    def get_formset(self, request, obj=None, **kwargs):
        FormSet = super().get_formset(request, obj, **kwargs)

        class CustomFormSet(FormSet):
            def __init__(self, *args, **kwargs):
                # Find related handover checklist for the booking obj
                handover = None
                if obj:
                    try:
                        # Assuming only one pickup handover checklist per booking
                        handover = obj.checklists.filter(checklist_type='pickup').first()
                    except Exception:
                        handover = None
                kwargs['form_kwargs'] = {'handover_instance': handover}
                super().__init__(*args, **kwargs)

        return CustomFormSet


class BookingAdmin(admin.ModelAdmin):
    form = BookingAdminForm
    list_display = ('booking_number', 'campervan', 'start_date', 'end_date', 'total_price', 'status', 'payment_status')
    list_filter = ('status', 'payment_status')
    search_fields = ('booking_number', 'primary_driver_name', 'additional_driver_name')
    readonly_fields = ('booking_number', 'total_price', 'created_at', 'updated_at', 'deposit_amount_display', 'render_signature_canvas')
    ordering = ('-created_at',)
    filter_horizontal = ('additional_services',)
    inlines = [HandoverChecklistInline, ReturnChecklistInline]


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

    def render_signature_canvas(obj, canvas_id_prefix="signature-canvas", hidden_input_id="id_signature_data"):
        obj_id = obj.pk if obj else 'new'
        canvas_id = f"{canvas_id_prefix}-{obj_id}"
        image_url = obj.customer_signature.url if obj and obj.customer_signature else ""

        existing_image_html = f"""
            <div style="margin-bottom: 10px;">
                <strong>Existing Signature:</strong><br>
                <img src="{image_url}" alt="Customer Signature" style="border:1px solid #000; max-width:400px; max-height:150px;">
            </div>
        """ if image_url else ""

        return mark_safe(f"""
            {existing_image_html}
            <label>Draw/Update Signature:</label><br>
            <canvas id="{canvas_id}" data-input="{hidden_input_id}" data-img="{image_url}" width="400" height="150" style="border:1px solid #000;"></canvas><br>
            <button type="button" class="clear-signature">Clear</button>
            <input type="hidden" name="signature_data" id="{hidden_input_id}">
        """)

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
admin.site.register(HandoverChecklist, HandoverChecklistAdmin)
