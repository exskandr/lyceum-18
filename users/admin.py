from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Додаткові поля', {'fields': ('role', 'phone_number')}),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        # автоматичне додавання користувача в групу згідно з роллю
        from django.contrib.auth.models import Group
        for group in Group.objects.all():
            obj.groups.remove(group)  # видаляємо з усіх груп

        group, created = Group.objects.get_or_create(name=obj.role)
        obj.groups.add(group)

