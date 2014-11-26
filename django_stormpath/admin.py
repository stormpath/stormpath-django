from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import StormpathUser
from .forms import StormpathUserCreationForm, StormpathUserChangeForm


class StormpathUserAdmin(UserAdmin):
    # Set the add/modify forms
    add_form = StormpathUserCreationForm
    form = StormpathUserChangeForm
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ("email", "is_staff", "given_name", 'surname')
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("email", "given_name", "surname")
    ordering = ("email",)
    filter_horizontal = ("groups", "user_permissions",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("given_name", "surname")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser",
            "groups",)}),
        ("Important dates", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",),
        "fields": ("given_name", "surname", "email", "password1", "password2")}),
    )

# Register the new CustomUserAdmin
admin.site.register(StormpathUser, StormpathUserAdmin)
