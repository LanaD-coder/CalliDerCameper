from django import forms
from django.forms import modelformset_factory
from django.utils.translation import gettext_lazy as _
from .models import Booking, HandoverChecklist, HandoverPhoto
from rentals.models import AdditionalService
import base64, uuid
from django.core.files.base import ContentFile


class BookingForm(forms.ModelForm):
    # Primary driver fields
    primary_driver_name = forms.CharField(required=False, label=_("Name"))
    primary_driver_street_name = forms.CharField(max_length=100, required=False, label=_("Street Name"))
    primary_driver_street_number = forms.CharField(max_length=10, required=False, label=_("Street Number"))
    primary_driver_postal_code = forms.CharField(max_length=20, required=False, label=_("Postal Code"))
    primary_driver_town = forms.CharField(max_length=100, required=False, label=_("Town/City"))
    primary_driver_country = forms.CharField(max_length=100, required=False, label=_("Country"))

    # Additional driver fields
    additional_driver_email = forms.EmailField(required=False, label=_("Additional Driver Email"))
    additional_driver_street = forms.CharField(required=False, label=_("Street"))
    additional_driver_postal_code = forms.CharField(required=False, label=_("Postal Code"))
    additional_driver_town = forms.CharField(required=False, label=_("Town/City"))
    additional_driver_country = forms.CharField(required=False, label=_("Country"))

    # Other custom fields
    discount_code = forms.CharField(max_length=50, required=False, label=_("Discount Code"))
    deposit = forms.BooleanField(
        required=False,
        label=_("Deposit (€1000) – Automatically applied"),
        initial=True,
        disabled=True
    )
    deposit_hidden = forms.BooleanField(widget=forms.HiddenInput(), initial=True)

    additional_services = forms.ModelMultipleChoiceField(
        queryset=AdditionalService.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Additional Services")
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.campervan = kwargs.pop('campervan', None)
        super().__init__(*args, **kwargs)

        if self.user and self.user.is_authenticated:
            self.fields['primary_driver_name'].initial = self.user.get_full_name() or self.user.username

    def clean(self):
        return super().clean()

    def save(self, commit=True):
        booking = super().save(commit=False)

        # Set address-related fields
        booking.primary_driver_name = self.cleaned_data.get('primary_driver_name', '')
        booking.primary_driver_street_name = self.cleaned_data.get('primary_driver_street_name', '')
        booking.primary_driver_street_number = self.cleaned_data.get('primary_driver_street_number', '')
        booking.primary_driver_postal_code = self.cleaned_data.get('primary_driver_postal_code', '')
        booking.primary_driver_town = self.cleaned_data.get('primary_driver_town', '')
        booking.primary_driver_country = self.cleaned_data.get('primary_driver_country', '')

        booking.additional_driver_street = self.cleaned_data.get('additional_driver_street', '')
        booking.additional_driver_postal_code = self.cleaned_data.get('additional_driver_postal_code', '')
        booking.additional_driver_town = self.cleaned_data.get('additional_driver_town', '')
        booking.additional_driver_country = self.cleaned_data.get('additional_driver_country', '')

        if self.user:
            booking.primary_driver = self.user
        if self.campervan:
            booking.campervan = self.campervan

        if commit:
            booking.save()
            self.save_m2m()

        return booking

    class Meta:
        model = Booking
        fields = [
            'start_date', 'end_date',
            'primary_driver_name', 'primary_driver_street_name', 'primary_driver_street_number',
            'primary_driver_postal_code', 'primary_driver_town', 'primary_driver_country',
            'additional_driver_name', 'additional_driver_email', 'additional_driver_contact_number',
            'additional_driver_street', 'additional_driver_postal_code', 'additional_driver_town',
            'additional_driver_country',
            'deposit_hidden', 'additional_services',
            'pickup_location', 'pickup_time', 'dropoff_location', 'dropoff_time',
            'customer_notes', 'cancellation_reason', 'refund_amount',
        ]
        widgets = {
            'start_date': forms.TextInput(attrs={'type': 'text', 'class': 'js-datepicker'}),
            'end_date': forms.TextInput(attrs={'type': 'text', 'class': 'js-datepicker'}),
            'pickup_time': forms.TimeInput(attrs={'type': 'time'}),
            'dropoff_time': forms.TimeInput(attrs={'type': 'time'}),
            'customer_notes': forms.Textarea(attrs={
                'rows': 1,
                'cols': 40,
                'class': 'form-control text-sm'
            }),
            'cancellation_reason': forms.Textarea(attrs={
                'rows': 1,
                'cols': 40,
                'class': 'form-control text-sm'
            }),
        }

class HandoverChecklistForm(forms.ModelForm):
    signature_data = forms.CharField(
        widget=forms.HiddenInput(attrs={'id': 'id_signature_data'}),
        required=False
    )
    photos = forms.FileField(
        widget=forms.ClearableFileInput(),
        required=False,
        label=_("Photos")
    )

    class Meta:
        model = HandoverChecklist
        fields = [
            'date', 'time', 'driver_name', 'phone_contact', 'odometer',
            'location', 'windshields', 'paintwork', 'bodywork',
            'tires_front', 'tires_rear', 'seats', 'upholstery',
            'windows', 'lights', 'flooring', 'known_damage', 'notes',
            'customer_signature'
        ]

        labels = {
            'date': _("Date"),
            'time': _("Time"),
            'driver_name': _("Driver Name"),
            'phone_contact': _("Phone Contact"),
            'odometer': _("Odometer"),
            'location': _("Location"),
            'windshields': _("Windshields"),
            'paintwork': _("Paintwork"),
            'bodywork': _("Bodywork"),
            'tires_front': _("Front Tires"),
            'tires_rear': _("Rear Tires"),
            'seats': _("Seats"),
            'upholstery': _("Upholstery"),
            'windows': _("Windows"),
            'lights': _("Lights"),
            'flooring': _("Flooring"),
            'known_damage': _("Known Damage"),
            'photos': _("Photos"),
            'notes': _("Notes"),
            'customer_signature': _("Customer Signature"),
        }
        widgets = {
            'customer_signature': forms.ClearableFileInput(),
            'checklist_type': forms.RadioSelect,
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'photos': forms.ClearableFileInput(attrs={'multiple': False}),
            'known_damage': forms.Textarea(attrs={
                'rows': 2,
                'cols': 40,
                'class': 'form-control text-sm'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 2,
                'cols': 40,
                'class': 'form-control text-sm'
            }),
            'location': forms.Textarea(attrs={
                'rows': 1,
                'cols': 40,
                'class': 'form-control text-sm'
            }),
        }

    def save(self, commit=True):
                instance = super().save(commit=False)
                sig_data = self.cleaned_data.get('signature_data')

                if sig_data:
                    try:
                        import base64, uuid
                        from django.core.files.base import ContentFile

                        format, imgstr = sig_data.split(';base64,')
                        ext = format.split('/')[-1]
                        filename = f"{uuid.uuid4()}.{ext}"
                        file = ContentFile(base64.b64decode(imgstr), name=filename)

                        # Save to checklist
                        instance.customer_signature.save(filename, file, save=False)

                        # Save to booking
                        if instance.booking:
                            instance.booking.customer_signature.save(filename, file, save=True)

                    except Exception as e:
                        print("Signature save error:", e)

                if commit:
                    instance.save()
                    self.save_m2m()

                return instance


class HandoverPhotoForm(forms.ModelForm):
    class Meta:
        model = HandoverPhoto
        fields = ['image']
        widgets = {
            'image': forms.ClearableFileInput(attrs={'multiple': False})
        }


HandoverPhotoFormSet = modelformset_factory(
    HandoverPhoto,
    form=HandoverPhotoForm,
    extra=3,
    can_delete=True
)

class ReturnChecklistForm(HandoverChecklistForm):
    initial_odometer = forms.IntegerField(
        label="Initial Odometer (from handover)",
        required=False,
        disabled=True,
    )

    def __init__(self, *args, **kwargs):
        handover_instance = kwargs.pop('handover_instance', None)
        super().__init__(*args, **kwargs)
        if handover_instance:
            self.fields['initial_odometer'].initial = handover_instance.odometer

    class Meta(HandoverChecklistForm.Meta):
        fields = HandoverChecklistForm.Meta.fields + ['initial_odometer']


class BookingAdminForm(forms.ModelForm):
    signature_data = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Booking
        fields = '__all__'

    def save(self, commit=True):
        instance = super().save(commit=False)
        sig_data = self.cleaned_data.get('signature_data')

        if sig_data:
            try:
                format, imgstr = sig_data.split(';base64,')
                ext = format.split('/')[-1]
                filename = f"{uuid.uuid4()}.{ext}"
                instance.customer_signature.save(filename, ContentFile(base64.b64decode(imgstr)), save=False)
            except Exception as e:
                print("Signature save error:", e)

        if commit:
            instance.save()
            self.save_m2m()
        return instance
