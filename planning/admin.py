from django.contrib import admin
from .models import CurriculumPlan, LessonTopic


class LessonTopicInline(admin.TabularInline):
    model = LessonTopic
    extra = 0
    fields = ('lesson_number', 'topic', 'homework', 'lesson_type',)


@admin.register(CurriculumPlan)
class CurriculumPlanAdmin(admin.ModelAdmin):
    list_display = ('subject', 'school_class', 'teacher', 'academic_year')
    list_filter = ('academic_year', 'subject', 'school_class', 'teacher')
    search_fields = ('subject__name', 'school_class__name', 'teacher__user__last_name')
    inlines = [LessonTopicInline] # Додаємо інлайн для тем уроків

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Вчитель бачить лише свої плани
        if request.user.is_teacher() and not request.user.is_superuser:
            return qs.filter(teacher__user=request.user)
        return qs


@admin.register(LessonTopic)
class LessonTopicAdmin(admin.ModelAdmin):
    list_display = ('lesson_number', 'topic', 'plan', 'lesson_type', 'homework')
    list_filter = ('lesson_type', 'plan__subject', 'plan__school_class')
    search_fields = ('topic', 'homework', 'plan__subject__name')
    raw_id_fields = ('plan',) # Використовувати ID замість випадаючого списку для плану

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_teacher() and not request.user.is_superuser:
            return qs.filter(plan__teacher__user=request.user)
        return qs