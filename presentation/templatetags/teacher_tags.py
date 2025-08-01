from django import template
from users.models import User # Переконайтеся, що шлях правильний

register = template.Library()


@register.inclusion_tag('teacher_tags/random_teachers.html')
def show_random_teachers():
    """
    Отримує 5 випадкових вчителів і передає їх для рендерингу в шаблоні.
    """
    random_teachers = User.objects.filter(role='teacher').order_by('?')[:5]
    return {'random_teachers': random_teachers}
