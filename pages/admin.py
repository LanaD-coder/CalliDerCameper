from django.contrib import admin
from .models import ( ContactMessage,
                    FAQ,
                    CampingDestination)

class CampingDestinationAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(ContactMessage)
admin.site.register(FAQ)
admin.site.register(CampingDestination)
