from django.urls import path
from . import views

app_name = 'teacher'

urlpatterns = [
    path('', views.teacher_list, name='teacher_list'),
    path('teacher/<int:pk>/', views.teacher_detail, name='teacher_detail'),
]
