from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile


# @admin.register(User)
# class CustomUserAdmin(UserAdmin):
#     fieldsets = UserAdmin.fieldsets + (
#         ('Додаткові поля', {'fields': ('role', 'phone_number')}),
#     )
#     list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
#     list_filter = ('role', 'is_staff', 'is_superuser')
#
#     def save_model(self, request, obj, form, change):
#         super().save_model(request, obj, form, change)
#
#         # автоматичне додавання користувача в групу згідно з роллю
#         from django.contrib.auth.models import Group
#         for group in Group.objects.all():
#             obj.groups.remove(group)  # видаляємо з усіх груп
#
#         group, created = Group.objects.get_or_create(name=obj.role)
#         obj.groups.add(group)

# Inline для моделі Profile
class ProfileInline(admin.StackedInline): # StackedInline відображає поля вертикально, TabularInline - в таблиці
    model = Profile
    can_delete = False # Заборонити видалення профілю без видалення користувача
    verbose_name_plural = 'Профіль' # Назва, яка відображатиметься в адмінці


# Розширюємо існуючий UserAdmin
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,) # Додаємо inline для профілю
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff') # Додаємо 'role' до списку
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active') # Додаємо 'role' до фільтрів
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (('Персональна інформація'), {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        (('Дозволи'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (('Важливі дати'), {'fields': ('last_login', 'date_joined')}),
        (('Роль'), {'fields': ('role',)}), # Додаємо поле ролі
    )

# Відреєструйте вашу кастомну модель User з вашим кастомним UserAdmin
# admin.site.unregister(User) # Спочатку розреєструйте базовий User, якщо він був зареєстрований
admin.site.register(User, UserAdmin)

# Якщо ви хочете, щоб Profile був доступний як окрема модель в адмінці (не тільки через User),
# то можете також зареєструвати його окремо, але це не є обов'язковим при використанні Inline.
# admin.site.register(Profile)