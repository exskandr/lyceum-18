from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('journal/<int:class_id>/<int:subject_id>/', views.teacher_journal, name='teacher_journal'),
    # TODO: Додати URL для оновлення оцінок/відвідуваності (через AJAX)
    path('update-grade/', views.update_grade, name='update_grade'),
    path('update-attendance/', views.update_attendance, name='update_attendance'),
]