# planning/admin.py
from django.contrib import admin
from .models import CurriculumPlan, LessonTopic, LessonDay, CurriculumUnit # Додаємо CurriculumUnit


@admin.register(LessonDay)
class LessonDayAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_name_display')
    ordering = ('id',) # Забезпечить, щоб дні відображалися у правильному порядку


@admin.register(CurriculumUnit)
class CurriculumUnitAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'plan', 'get_plan_info')
    list_filter = ('plan__teacher', 'plan__school_class', 'plan__subject', 'plan__academic_year')
    search_fields = ('title', 'plan__subject__name', 'plan__school_class__letter_designation')
    raw_id_fields = ('plan',) # Використовуватиме зручний віджет для вибору CurriculumPlan
    ordering = ('plan__academic_year', 'plan__school_class__start_year', 'plan__school_class__letter_designation', 'order')

    def get_plan_info(self, obj):
        return f"{obj.plan.subject.name} - {obj.plan.school_class.full_name()} ({obj.plan.academic_year})"
    get_plan_info.short_description = "Календарний план"


# Клас для інлайн-редагування LessonTopic всередині CurriculumPlan
class LessonTopicInline(admin.TabularInline):
    model = LessonTopic
    extra = 0 # Не показувати порожні форми для нових об'єктів
    fields = ('lesson_number', 'topic', 'lesson_type', 'group', 'homework', 'curriculum_unit')
    raw_id_fields = ('curriculum_unit',) # Дозволяє вибрати CurriculumUnit зі списку, якщо їх багато
    ordering = ('lesson_number',)


@admin.register(CurriculumPlan)
class CurriculumPlanAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'teacher', 'school_class', 'subject', 'academic_year')
    list_filter = ('teacher', 'school_class', 'subject', 'academic_year')
    search_fields = ('teacher__user__last_name', 'school_class__letter_designation', 'subject__name', 'academic_year')
    date_hierarchy = 'academic_year_start'
    filter_horizontal = ('lesson_frequency_days',) # Зручний віджет для ManyToMany поля
    fieldsets = (
        (None, {
            'fields': ('teacher', 'school_class', 'subject', 'academic_year')
        }),
        ('Періоди навчання', {
            'fields': (
                'academic_year_start', 'academic_year_end',
                'semester_1_start', 'semester_1_end',
                'semester_2_start', 'semester_2_end'
            ),
            'classes': ('collapse',), # Зробити згортаним
        }),
        ('Налаштування уроків', {
            'fields': ('lesson_frequency_days', 'vacation_periods_json'),
            'classes': ('collapse',),
        }),
    )
    inlines = [LessonTopicInline] # Дозволяє редагувати LessonTopic безпосередньо з CurriculumPlan


@admin.register(LessonTopic)  # Якщо ви хочете керувати LessonTopic окремо, а не тільки через CurriculumPlan
class LessonTopicAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'plan', 'lesson_number', 'topic', 'lesson_type', 'group')
    list_filter = ('plan__school_class', 'plan__subject', 'plan__teacher', 'lesson_type', 'group', 'curriculum_unit')
    search_fields = ('topic', 'homework', 'plan__subject__name', 'plan__school_class__letter_designation')
    raw_id_fields = ('plan', 'curriculum_unit')
    ordering = ('plan__academic_year', 'plan__school_class__start_year', 'plan__school_class__letter_designation', 'lesson_number')