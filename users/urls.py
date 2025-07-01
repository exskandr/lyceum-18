from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('profile/', views.profile_view, name='profile'),
   # path('login/', LoginView.as_view(template_name='/login.html'), name='login'),
   # path('logout/', LogoutView.as_view(), name='logout'),
]
