from django.contrib import admin
from .models import Lesson, Grade, Attendance


class GradeInline(admin.TabularInline):
    model = Grade
    extra = 0
    fields = ('student', 'value', 'grade_type', 'comment')
    raw_id_fields = ('student',) # Краще для великої кількості учнів


class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 0
    fields = ('student', 'is_present', 'reason')
    raw_id_fields = ('student',) # Краще для великої кількості учнів


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('date', 'subject', 'school_class', 'teacher', 'get_lesson_topic')
    list_filter = ('date', 'subject', 'school_class', 'teacher')
    search_fields = ('lesson_topic__topic', 'subject__name', 'school_class__name', 'teacher__user__last_name')
    raw_id_fields = ('lesson_topic', 'teacher', 'school_class', 'subject') # Зручно для вибору існуючих об'єктів
    inlines = [GradeInline, AttendanceInline] # Додаємо інлайни для оцінок та відвідуваності

    def get_lesson_topic(self, obj):
        return obj.lesson_topic.topic
    get_lesson_topic.short_description = "Тема уроку"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Вчитель бачить лише свої уроки
        if request.user.is_teacher() and not request.user.is_superuser:
            return qs.filter(teacher__user=request.user)
        return qs


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'value', 'grade_type', 'comment')
    list_filter = ('grade_type', 'lesson__subject', 'lesson__school_class', 'student__school_class')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'lesson__lesson_topic__topic')
    raw_id_fields = ('student', 'lesson')  # Краще для вибору об'єктів

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_teacher() and not request.user.is_superuser:
            # Вчитель бачить лише оцінки зі своїх уроків
            return qs.filter(lesson__teacher__user=request.user)
        elif request.user.is_student() and not request.user.is_superuser:
            # Учень бачить лише свої оцінки
            return qs.filter(student__user=request.user)
        elif request.user.is_parent() and not request.user.is_superuser:
            # Батько бачить оцінки своїх дітей
            return qs.filter(student__parents__user=request.user).distinct()
        return qs


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'lesson', 'is_present', 'reason')
    list_filter = ('is_present', 'lesson__subject', 'lesson__school_class', 'student__school_class')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'reason')
    raw_id_fields = ('student', 'lesson') # Краще для вибору об'єктів

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_teacher() and not request.user.is_superuser:
            # Вчитель бачить лише відвідуваність зі своїх уроків
            return qs.filter(lesson__teacher__user=request.user)
        return qs
