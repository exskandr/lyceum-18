from django.urls import path
from . import views
from .feeds import LatestNewsFeed

app_name = 'news'

urlpatterns = [
    path('', views.home, name='home'),
    path('news/', views.news_list, name='news_list'),  # Список новин
    path('tag/<slug:tag_slug>/', views.news_list, name='news_list_by_tag'),
    path(
        '<int:year>/<int:month>/<int:day>/<slug:news>/',
        views.news_detail,
        name='news_detail'),  # Детальна новина
    path('feed/', LatestNewsFeed(), name='news_feed'),
    path('pages/<slug:slug>/', views.DynamicPageView.as_view(), name='dynamic_page'),
    path('calls_schedule/', views.call_schedule, name='calls_schedule'),
    path('lessons_schedule/', views.lessons_schedule, name='lessons_schedule')
]
