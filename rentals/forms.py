from django import forms
from .models import Booking


class BookingForm(forms.ModelForm):
    primary_driver_name = forms.CharField(required=False, disabled=True)
    primary_driver_address = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False, disabled=True)

    # New additional driver expanded fields (not in model)
    additional_driver_email = forms.EmailField(required=False)
    additional_driver_street = forms.CharField(required=False)
    additional_driver_postal_code = forms.CharField(required=False)
    additional_driver_town = forms.CharField(required=False)
    additional_driver_country = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.campervan = kwargs.pop('campervan', None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields['primary_driver_name'].initial = self.user.get_full_name()
            if hasattr(self.user, 'userprofile'):
                profile = self.user.userprofile
                addr = f"{profile.street}\n{profile.postal_code} {profile.town}\n{profile.country}"
                self.fields['primary_driver_address'].initial = addr

        # Optionally set initial data for additional driver fields if available

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        # Validate dates
        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError("End date cannot be before start date.")

        add_driver = self.data.get('add_additional_driver', 'no')

        if add_driver == 'yes':
            # Validate additional driver fields
            name = cleaned_data.get('additional_driver_name')
            email = cleaned_data.get('additional_driver_email')
            contact = cleaned_data.get('additional_driver_contact_number')
            street = cleaned_data.get('additional_driver_street')
            postal_code = cleaned_data.get('additional_driver_postal_code')
            town = cleaned_data.get('additional_driver_town')
            country = cleaned_data.get('additional_driver_country')

            # Name required
            if not name:
                self.add_error('additional_driver_name', "Name is required for additional driver.")
            # Contact number required
            if not contact:
                self.add_error('additional_driver_contact_number', "Contact number is required for additional driver.")
            # Email required
            if not email:
                self.add_error('additional_driver_email', "Email is required for additional driver.")
            # Address fields required
            if not all([street, postal_code, town, country]):
                msg = "Complete address is required for additional driver."
                if not street:
                    self.add_error('additional_driver_street', msg)
                if not postal_code:
                    self.add_error('additional_driver_postal_code', msg)
                if not town:
                    self.add_error('additional_driver_town', msg)
                if not country:
                    self.add_error('additional_driver_country', msg)

            # Existing license and age checks
            has_license = cleaned_data.get('additional_driver_has_license')
            over_21 = cleaned_data.get('additional_driver_over_21')

            if not has_license:
                self.add_error('additional_driver_has_license', "You must confirm the additional driver has a valid driver's license.")
            if not over_21:
                self.add_error('additional_driver_over_21', "Additional driver must be over 21 years old.")
        else:
            # Clear additional driver fields if not adding
            cleaned_data['additional_driver_name'] = ''
            cleaned_data['additional_driver_email'] = ''
            cleaned_data['additional_driver_contact_number'] = ''
            cleaned_data['additional_driver_street'] = ''
            cleaned_data['additional_driver_postal_code'] = ''
            cleaned_data['additional_driver_town'] = ''
            cleaned_data['additional_driver_country'] = ''
            cleaned_data['additional_driver_has_license'] = False
            cleaned_data['additional_driver_over_21'] = False

        return cleaned_data

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
            'additional_driver_name', 'additional_driver_contact_number',
            'additional_driver_has_license', 'additional_driver_over_21',
            'additional_insurance', 'additional_services'
        ]
        widgets = {
            'additional_driver_address': forms.Textarea(attrs={'rows': 2}),  # You may remove this field from model/form if not used
            'additional_services': forms.CheckboxSelectMultiple(),
        }
