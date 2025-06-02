from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, DiscountCode

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'percentage_display', 'active', 'valid_from', 'valid_to')
    list_filter = ('active',)
    search_fields = ('code',)

    def percentage_display(self, obj):
        return f"{obj.percentage}%"
    percentage_display.short_description = 'Discount Percentage'

# Re-register UserAdmin to reset django builtin usermodel
admin.site.register(DiscountCode)
admin.site.unregister(User)
admin.site.register(User, UserAdmin)