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

    deposit = forms.BooleanField(
        required=False,
        label="Deposit (€1000) – Automatically applied",
        initial=True,
        disabled=True
    )
    deposit_hidden = forms.BooleanField(widget=forms.HiddenInput(), initial=True)

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
            full_name = self.user.get_full_name()
            if full_name:
                self.fields['primary_driver_name'].initial = full_name
            else:
                self.fields['primary_driver_name'].initial = self.user.username

    def clean(self):
        cleaned_data = super().clean()
        # Your validation code here ...
        return cleaned_data

    def save(self, commit=True):
        booking = super().save(commit=False)

        # Compose primary driver address parts from cleaned_data
        p_street = self.cleaned_data.get('primary_driver_street_name', '')
        p_number = self.cleaned_data.get('primary_driver_street_number', '')
        p_postal = self.cleaned_data.get('primary_driver_postal_code', '')
        p_town = self.cleaned_data.get('primary_driver_town', '')
        p_country = self.cleaned_data.get('primary_driver_country', '')

        booking.primary_driver_street_number = p_number
        booking.primary_driver_postal_code = p_postal
        booking.primary_driver_town = p_town
        booking.primary_driver_country = p_country

        # Compose additional driver address parts
        street = self.cleaned_data.get('additional_driver_street', '')
        postal = self.cleaned_data.get('additional_driver_postal_code', '')
        town = self.cleaned_data.get('additional_driver_town', '')
        country = self.cleaned_data.get('additional_driver_country', '')

        # Assign additional driver address parts back to the booking fields
        booking.additional_driver_street = street
        booking.additional_driver_postal_code = postal
        booking.additional_driver_town = town
        booking.additional_driver_country = country

        # Save manual primary driver name
        booking.primary_driver_name = self.cleaned_data.get('primary_driver_name', '')

        # Set foreign keys if available
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
