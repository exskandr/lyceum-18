import markdown
from django.contrib.syndication.views import Feed
from django.template.defaultfilters import truncatewords_html
from django.urls import reverse_lazy
from .models import News


class LatestNewsFeed(Feed):

    title = 'News Lyceum №18'
    link = reverse_lazy('news:news_list')
    description = 'New news on lyceum.'

    def items(self):
        return News.published.all()[:3]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return truncatewords_html(markdown.markdown(item.content), 30)

    def item_pubdate(self, item):
        return item.publish