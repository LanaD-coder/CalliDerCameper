from django import forms
from .models import Booking

class BookingForm(forms.ModelForm):
    primary_driver_name = forms.CharField(required=False, disabled=True)
    primary_driver_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False, disabled=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.campervan = kwargs.pop('campervan', None)
        super().__init__(*args, **kwargs)

        # Set primary driver fields for display
        if self.user:
            self.fields['primary_driver_name'].initial = self.user.get_full_name()
            if hasattr(self.user, 'userprofile'):
                self.fields['primary_driver_address'].initial = self.user.userprofile.address

    def save(self, commit=True):
        booking = super().save(commit=False)
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
            'additional_driver_name', 'additional_driver_address', 'additional_driver_contact_number',
            'additional_driver_has_license', 'additional_driver_over_21',
            'additional_insurance', 'additional_services'
        ]
        widgets = {
            'additional_driver_address': forms.Textarea(attrs={'rows': 2}),
            'additional_services': forms.CheckboxSelectMultiple(),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        # Date validation
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError("End date cannot be before start date.")

        # Additional driver validations
        name = cleaned_data.get('additional_driver_name')
        contact = cleaned_data.get('additional_driver_contact_number')
        has_license = cleaned_data.get('additional_driver_has_license')
        over_21 = cleaned_data.get('additional_driver_over_21')

        if name:
            if not contact:
                self.add_error('additional_driver_contact_number', "Contact number is required for additional driver.")
            if not has_license:
                self.add_error('additional_driver_has_license', "You must confirm the additional driver has a valid driver's license.")
            if not over_21:
                self.add_error('additional_driver_over_21', "Additional driver must be over 21 years old.")
        else:
            # If no additional driver name, clear out dependent fields
            cleaned_data['additional_driver_contact_number'] = None
            cleaned_data['additional_driver_has_license'] = False
            cleaned_data['additional_driver_over_21'] = False

        return cleaned_data
