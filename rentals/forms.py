from django.forms import modelformset_factory
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Booking, HandoverChecklist, HandoverPhoto
from rentals.models import AdditionalService


class BookingForm(forms.ModelForm):
    primary_driver_name = forms.CharField(required=False, label=_("Name"))
    primary_driver_street_name = forms.CharField(max_length=100, required=False, label=_("Street Name"))
    primary_driver_street_number = forms.CharField(max_length=10, required=False, label=_("Street Number"))
    primary_driver_postal_code = forms.CharField(max_length=20, required=False, label=_("Postal Code"))
    primary_driver_town = forms.CharField(max_length=100, required=False, label=_("Town/City"))
    primary_driver_country = forms.CharField(max_length=100, required=False, label=_("Country"))

    additional_driver_email = forms.EmailField(required=False, label=_("Additional Driver Email"))
    additional_driver_street = forms.CharField(required=False, label=_("Street"))
    additional_driver_postal_code = forms.CharField(required=False, label=_("Postal Code"))
    additional_driver_town = forms.CharField(required=False, label=_("Town/City"))
    additional_driver_country = forms.CharField(required=False, label=_("Country"))
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
            full_name = self.user.get_full_name()
            if full_name:
                self.fields['primary_driver_name'].initial = full_name
            else:
                self.fields['primary_driver_name'].initial = self.user.username

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def save(self, commit=True):
        booking = super().save(commit=False)

        # Compose primary driver address
        booking.primary_driver_street_number = self.cleaned_data.get('primary_driver_street_number', '')
        booking.primary_driver_postal_code = self.cleaned_data.get('primary_driver_postal_code', '')
        booking.primary_driver_town = self.cleaned_data.get('primary_driver_town', '')
        booking.primary_driver_country = self.cleaned_data.get('primary_driver_country', '')

        # Compose additional driver address
        booking.additional_driver_street = self.cleaned_data.get('additional_driver_street', '')
        booking.additional_driver_postal_code = self.cleaned_data.get('additional_driver_postal_code', '')
        booking.additional_driver_town = self.cleaned_data.get('additional_driver_town', '')
        booking.additional_driver_country = self.cleaned_data.get('additional_driver_country', '')

        booking.primary_driver_name = self.cleaned_data.get('primary_driver_name', '')

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

            'primary_driver_name',
            'primary_driver_street_name',
            'primary_driver_street_number',
            'primary_driver_postal_code',
            'primary_driver_town',
            'primary_driver_country',

            'additional_driver_name', 'additional_driver_email', 'additional_driver_contact_number',
            'additional_driver_street', 'additional_driver_postal_code', 'additional_driver_town', 'additional_driver_country',

            'deposit_hidden', 'additional_services',

            'pickup_location', 'pickup_time', 'dropoff_location', 'dropoff_time',

            'customer_notes',

            'cancellation_reason', 'refund_amount',
        ]
        widgets = {
            'additional_driver_address': forms.Textarea(attrs={'rows': 2}),
            'start_date': forms.TextInput(attrs={'type': 'text', 'class': 'js-datepicker'}),
            'end_date': forms.TextInput(attrs={'type': 'text', 'class': 'js-datepicker'}),
            'pickup_time': forms.TimeInput(attrs={'type': 'time'}),
            'dropoff_time': forms.TimeInput(attrs={'type': 'time'}),
            'additional_services': forms.CheckboxSelectMultiple(),
        }


class HandoverChecklistForm(forms.ModelForm):
    class Meta:
        model = HandoverChecklist
        fields = [
            'checklist_type', 'date', 'time', 'driver_name', 'phone_contact', 'odometer',
            'location', 'windshields', 'paintwork', 'bodywork',
            'tires_front', 'tires_rear', 'seats', 'upholstery',
            'windows', 'lights', 'flooring', 'known_damage', 'notes'
        ]
        widgets = {
            'checklist_type': forms.RadioSelect,
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
            'photos': forms.ClearableFileInput(attrs={'multiple': False}),
        }


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
        label=_("Initial Odometer (from handover)"),
        required=False,
        disabled=True,
    )

    def __init__(self, *args, **kwargs):
        # Accept related handover instance to fetch odometer
        handover_instance = kwargs.pop('handover_instance', None)
        super().__init__(*args, **kwargs)

        if handover_instance:
            self.fields['initial_odometer'].initial = handover_instance.odometer

    class Meta(HandoverChecklistForm.Meta):
        fields = HandoverChecklistForm.Meta.fields + ['initial_odometer']