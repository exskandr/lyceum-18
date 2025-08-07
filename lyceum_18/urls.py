"""
URL configuration for lyceum_18 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', include('presentation.urls', namespace='presentation')),
    # path('', TemplateView.as_view(template_name='home.html'), name='home'), # Домашня сторінка ліцею
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    # path('', include('frontend.urls')),
    path('teacher/', include('frontend.urls')),  # Включаємо URL-и додатку frontend

    # path('student/', include('frontend.urls')), # Додасте пізніше
    # path('parent/', include('frontend.urls')), # Додасте пізніше

    path('', include('presentation.urls', namespace='presentation')),
    path('news/', include('presentation.news_urls', namespace='news')),
    path('teachers/', include('presentation.teacher_urls', namespace='teacher')),
    path('users/', include('users.urls')),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
