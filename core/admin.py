from django.contrib import admin
from django.utils import timezone
from django.template.response import TemplateResponse
from django.urls import path
from django.contrib import messages

from .models import SchoolClass, Subject, Teacher, Student, Parent


class StudentInline(admin.TabularInline):
    model = Student
    extra = 0 # Не показувати порожні форми для додавання
    fk_name = 'school_class' # Вказуємо, який ForeignKey використовується


# Інлайн для дітей у батька (щоб бачити дітей прямо у батька)
class ChildInline(admin.TabularInline):
    model = Parent.children.through  # Для ManyToManyField використовуємо .through модель
    extra = 0
    verbose_name = "Дитина"
    verbose_name_plural = "Діти"


# --- Модельні Адмінки ---

@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = (
        'get_full_name', # Динамічна назва: "9-А"
        'letter_designation',
        'start_year',
        'status',
        'get_curator_name',
        'student_count'
    )
    list_filter = ('status', 'start_year', 'letter_designation')
    search_fields = (
        'letter_designation',
        'start_year',
        'curator__user__first_name',
        'curator__user__last_name'
    )
    inlines = [StudentInline] # Інлайн для студентів залишається

    # Додаємо поле для редагування статусу
    fieldsets = (
        (None, {
            'fields': ('letter_designation', 'start_year', 'status', 'curator')
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('update-statuses/',
                 self.admin_site.admin_view(self.update_class_statuses_view),
                 name='update_class_statuses'),
        ]
        return custom_urls + urls

    def update_class_statuses_view(self, request):
        if not request.user.is_superuser:
            self.message_user(request, "У вас немає дозволу на виконання цієї дії.", level=messages.ERROR)
            from django.shortcuts import redirect
            return redirect('..')
        # if not request.user.is_superuser:
        #     self.message_user(request, "У вас немає дозволу на виконання цієї дії.", level='error')
        #     return self.response_for_action(request, messages.ERROR, "У вас немає дозволу на виконання цієї дії.", None)
        #
        updated_count = 0
        for school_class in SchoolClass.objects.filter(status='active'):
            if school_class.update_status_based_on_grade():
                updated_count += 1

        from django.shortcuts import redirect
        self.message_user(request, f"Оновлено статусів для {updated_count} класів.", level=messages.SUCCESS)
        return redirect('..')
        #
        # self.message_user(request, f"Оновлено статусів для {updated_count} класів.", level='success')
        # # Перенаправлення на сторінку списку класів
        # return self.response_action_success(request, messages.SUCCESS, f"Оновлено статусів для {updated_count} класів.")

    def get_full_name(self, obj):
        return obj.full_name() # Використовуємо новий метод full_name
    get_full_name.short_description = "Повна назва класу"
    get_full_name.admin_order_field = 'start_year' # Дозволяє сортувати за роком початку

    def get_curator_name(self, obj):
        return obj.curator.user.get_full_name() if obj.curator else 'Не призначено'
    get_curator_name.short_description = "Класний керівник"

    def student_count(self, obj):
        return obj.students.count()
    student_count.short_description = "Кількість учнів"


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'get_taught_subjects', 'get_taught_classes', 'get_led_class')
    search_fields = ('user__first_name', 'user__last_name', 'subjects__name', 'classes__name')
    # Поля, які можна редагувати у формі вчителя
    filter_horizontal = ('subjects', 'classes',)    # Зручніший інтерфейс для M2M полів

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = "ПІБ Вчителя"

    def get_taught_subjects(self, obj):
        return ", ".join([subject.name for subject in obj.subjects.all()])
    get_taught_subjects.short_description = "Викладає предмети"

    def get_taught_classes(self, obj):
        return ", ".join([cls.full_name() for cls in obj.classes.all()])
    get_taught_classes.short_description = "Викладає в класах"

    def get_led_class(self, obj):
        # Отримання класу, де вчитель є класним керівником
        return obj.curator.full_name() if hasattr(obj, 'curator') else 'Не є класним керівником'
    get_led_class.short_description = "Класний керівник"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'school_class', 'get_parents')
    list_filter = ('school_class',)
    search_fields = ('user__first_name', 'user__last_name', 'school_class__name')

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = "ПІБ Учня"

    def get_parents(self, obj):
        return ", ".join([p.user.get_full_name() for p in obj.parents.all()])
    get_parents.short_description = "Батьки"


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'get_children_names')
    search_fields = ('user__first_name', 'user__last_name', 'children__user__first_name', 'children__user__last_name')
    filter_horizontal = ('children',) # Зручніший інтерфейс для ManyToManyField
    inlines = [ChildInline] # Додаємо інлайн для дітей

    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = "ПІБ Батька"

    def get_children_names(self, obj):
        return ", ".join([child.user.get_full_name() for child in obj.children.all()])
    get_children_names.short_description = "Діти"
