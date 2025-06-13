from django.urls import path
from . import views
urlpatterns = [
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('journal/<int:class_id>/<int:subject_id>/', views.teacher_journal, name='teacher_journal'),

    # URL для оновлення оцінок/відвідуваності (через AJAX)
    path('update-grade/', views.update_grade, name='update_grade'),
    path('update-attendance/', views.update_attendance, name='update_attendance'),

    # URL для сторінки налаштувань планування (де генеруємо/редагуємо CurriculumPlan)
    path('teacher/planning/<int:class_id>/<int:subject_id>/settings/', views.teacher_planning_settings_view,
         name='teacher_planning_settings_view'),

    # URL для відображення згенерованих уроків плану та їх редагування
    path('teacher/planning/<int:class_id>/<int:subject_id>/detail/', views.teacher_curriculum_detail_view,
         name='teacher_curriculum_detail_view'),

    # AJAX ендпоінти
    path('teacher/planning/<int:class_id>/<int:subject_id>/generate_lessons/', views.generate_lessons_for_plan,
         name='generate_lessons_for_plan'),
    path('teacher/planning/<int:class_id>/<int:subject_id>/save_plan_and_lessons/', views.save_plan_and_lessons,
         name='save_plan_and_lessons'),

]

