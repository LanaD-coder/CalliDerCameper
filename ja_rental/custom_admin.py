from django.contrib.admin import AdminSite
from rentals.models import (
    Campervan,
    Booking,
    SeasonalRate,
    CampervanImage,
    AdditionalService,
    Invoice,
    HandoverPhoto,
    HandoverChecklist,
    ReturnChecklist
)
from rentals.admin import BookingAdmin
from pages.models import ContactMessage, FAQ, CampingDestination
from accounts.models import UserProfile, DiscountCode


class CustomAdminSite(AdminSite):
    site_header = "Calli der Camper Admin"
    site_title = "My Project Admin Portal"
    index_title = "Welcome to the Admin"

    def get_app_list(self, request):
        app_list = super().get_app_list(request)

        app_order = ['rentals', 'pages', 'accounts', 'auth']

        def app_sort_key(app):
            try:
                return app_order.index(app['app_label'])
            except ValueError:
                return len(app_order) + 1

        app_list.sort(key=app_sort_key)

        for app in app_list:
            if app['app_label'] == 'rentals':
                model_order = [
                    'Booking','Campervan', 'SeasonalRate', 'AdditionalService', 'Invoice', 'FAQ'
                ]
                app['models'].sort(
                    key=lambda m: model_order.index(m['object_name']) if m['object_name'] in model_order else len(model_order) + 1
                )

        return app_list


# Create the single instance of your custom admin site
custom_admin_site = CustomAdminSite(name='customadmin')

# Register models with your custom admin site instance
custom_admin_site.register(Booking, BookingAdmin)
custom_admin_site.register(HandoverPhoto)
custom_admin_site.register(Campervan)
custom_admin_site.register(SeasonalRate)
custom_admin_site.register(AdditionalService)
custom_admin_site.register(Invoice)
custom_admin_site.register(ContactMessage)
custom_admin_site.register(FAQ)
custom_admin_site.register(CampingDestination)
custom_admin_site.register(UserProfile)
custom_admin_site.register(DiscountCode)
