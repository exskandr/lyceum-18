from django.urls import path
from . import views
from .feeds import LatestNewsFeed

app_name = 'news'

urlpatterns = [
    path('', views.news_list, name='news_list'),
    path('tag/<slug:tag_slug>/', views.news_list, name='news_list_by_tag'),
    path(
        '<int:year>/<int:month>/<int:day>/<slug:news>/',
        views.news_detail,
        name='news_detail'),
    path('feed/', LatestNewsFeed(), name='news_feed'),
]