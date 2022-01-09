from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


class UsersAdmin(UserAdmin):
    """
    User management in the Django Admin Panel.
    Available functions (to the Administrator):
    1. Changing the user password
    2. Changing the user profile
    3. Search by name and email
    4. Filter by email and last name
    5. Blocking the user
    6. Account Deletion
    Attention:
    Please note that login and email are case-insensitive.
    """
    list_display = ('username', 'email',
                    'first_name', 'last_name', 'role')
    fieldsets = (("User",
                 {"fields": (
                     'username', 'password', 'email',
                     'first_name', 'last_name',
                     'role', 'last_login', 'date_joined')}),)
    add_fieldsets = (("User",
                     {"fields": (
                         'username', 'password', 'email',
                         'first_name', 'last_name', 'role')}),)
    search_fields = ('first_name', 'email',)
    list_filter = ('email', 'first_name',)


admin.site.register(User, UsersAdmin)
