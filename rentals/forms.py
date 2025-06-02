from django import forms
from .models import Booking
from rentals.models import AdditionalService


class BookingForm(forms.ModelForm):
    # If you want primary driver manual fields editable
    primary_driver_name = forms.CharField(required=False)
    primary_driver_street_name = forms.CharField(max_length=100, required=False, label="Street Name")
    primary_driver_street_number = forms.CharField(max_length=10, required=False, label="Street Number")
    primary_driver_postal_code = forms.CharField(max_length=20, required=False, label="Postal Code")
    primary_driver_town = forms.CharField(max_length=100, required=False, label="Town/City")
    primary_driver_country = forms.CharField(max_length=100, required=False, label="Country")

    # Additional driver expanded fields NOT in model
    additional_driver_email = forms.EmailField(required=False)
    additional_driver_street = forms.CharField(required=False)
    additional_driver_postal_code = forms.CharField(required=False)
    additional_driver_town = forms.CharField(required=False)
    additional_driver_country = forms.CharField(required=False)
    discount_code = forms.CharField(max_length=50, required=False)

    additional_insurance = forms.BooleanField(
        required=False,
        label="Add Additional Insurance (€20)"
    )

    additional_services = forms.ModelMultipleChoiceField(
    queryset=AdditionalService.objects.all(),
    widget=forms.CheckboxSelectMultiple,
    required=False,
    label="Additional Services"
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.campervan = kwargs.pop('campervan', None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields['primary_driver_name'].initial = self.user.get_full_name()
            if hasattr(self.user, 'userprofile'):
                profile = self.user.userprofile
                addr = f"{profile.street}\n{profile.postal_code} {profile.town}\n{profile.country}"
                self.fields['primary_driver_address_manual'].initial = addr

    def clean(self):
        cleaned_data = super().clean()
        # Your validation code here ...
        return cleaned_data

    def save(self, commit=True):
        booking = super().save(commit=False)

        # Compose additional driver full address
        street = self.cleaned_data.get('additional_driver_street', '')
        postal = self.cleaned_data.get('additional_driver_postal_code', '')
        town = self.cleaned_data.get('additional_driver_town', '')
        country = self.cleaned_data.get('additional_driver_country', '')
        address_parts = [street, postal, town, country]
        full_address = '\n'.join(filter(None, address_parts))
        booking.additional_driver_address = full_address

        # Save manual primary driver info
        booking.primary_driver_name = self.cleaned_data.get('primary_driver_name', '')
        booking.primary_driver_address_manual = self.cleaned_data.get('primary_driver_address_manual', '')

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

            'primary_driver_name', 'primary_driver_address_manual',

            'additional_driver_name', 'additional_driver_email', 'additional_driver_contact_number',
            'additional_driver_street', 'additional_driver_postal_code', 'additional_driver_town', 'additional_driver_country',
            'additional_driver_license_number', 'additional_driver_license_expiry', 'additional_driver_has_license', 'additional_driver_over_21',

            'additional_insurance', 'additional_services',

            'pickup_location', 'pickup_time', 'dropoff_location', 'dropoff_time',

            'customer_notes',

            'cancellation_reason', 'refund_amount',
        ]
        widgets = {
            'primary_driver_address_manual': forms.Textarea(attrs={'rows': 2}),
            'additional_driver_address': forms.Textarea(attrs={'rows': 2}),
            'additional_driver_license_expiry': forms.DateInput(attrs={'type': 'date'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'pickup_time': forms.TimeInput(attrs={'type': 'time'}),
            'dropoff_time': forms.TimeInput(attrs={'type': 'time'}),
            'additional_services': forms.CheckboxSelectMultiple(),
        }
