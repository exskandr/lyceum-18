import markdown
from django.utils.safestring import mark_safe
from django import template
from ..models import News


register = template.Library()


@register.inclusion_tag('presentation/news/latest_news.html')
def show_latest_news(count=3):
    latest_news = News.published.order_by('-publish')[:count]
    return {'latest_news': latest_news}


@register.filter(name='markdown')
def markdown_format(text):
    return mark_safe(markdown.markdown(text))
