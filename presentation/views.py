from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from taggit.models import Tag
from users.models import User
from .models import News, NavbarSubItem, DynamicPage
from django.views.generic import DetailView
from django.db.models import F
from django.db.models.functions import Upper, Substr
import string


class DynamicPageView(DetailView):
    model = DynamicPage
    template_name = 'presentation/dynamic_page.html'
    context_object_name = 'page'

    def get_object(self):
        return get_object_or_404(DynamicPage, slug=self.kwargs['slug'])


def index(request):
    """
    Відображає головну сторінку візитної картки ліцею.
    """
    # sub_items = NavbarSubItem.objects.all().order_by('order')
    # navbar = {}
    # for category_key, category_label in NavbarSubItem.MAIN_CATEGORIES:
    #     navbar[category_key] = {
    #         'label': category_label,
    #         'sub_items': sub_items.filter(category=category_key),
    #     }

    return render(
        request,
        'presentation/index.html',
    )


def teacher_list(request):
    # Генеруємо список букв алфавіту для пошуку
    available_letters = User.objects.filter(
        role='teacher',
        last_name__isnull=False
    ).annotate(
        initial=Upper(Substr('last_name', 1, 1))
    ).values_list(
        'initial', flat=True
    ).distinct().order_by('initial')

    # Отримуємо обрану літеру з URL
    selected_letter = request.GET.get('letter')

    # Отримуємо всіх вчителів і сортуємо їх
    teachers_list = User.objects.filter(role='teacher').order_by(F('last_name').asc(nulls_last=True))

    if selected_letter:
        teachers_list = teachers_list.filter(last_name__istartswith=selected_letter)

    # Додаємо пагінацію
    paginator = Paginator(teachers_list, 3)  # 12 вчителів на сторінку
    page_number = request.GET.get('page')

    try:
        teachers = paginator.page(page_number)
    except PageNotAnInteger:
        teachers = paginator.page(1)
    except EmptyPage:
        teachers = paginator.page(paginator.num_pages)

    context = {
        'teachers': teachers,
        'available_letters': available_letters,
        'selected_letter': selected_letter,
    }
    return render(request, 'presentation/teacher/teacher_list.html', context)


def teacher_detail(request, pk):
    # Отримуємо об'єкт вчителя, або повертаємо 404, якщо не знайдено
    teacher = get_object_or_404(User, pk=pk, role='teacher')

    # Перевіряємо, чи існує пов'язаний об'єкт профілю
    # Це важливо, щоб уникнути помилок, якщо у користувача немає профілю
    if not hasattr(teacher, 'profile'):
        # Можна перенаправити або відобразити сторінку з помилкою
        # Наприклад, teacher_detail.html може обробляти цей випадок
        teacher.profile = None

    context = {
        'teacher': teacher,
    }
    return render(request, 'presentation/teacher/teacher_detail.html', context)


def home(request):
    sub_items = NavbarSubItem.objects.all().order_by('order')
    navbar = {}
    for category, label in NavbarSubItem.MAIN_CATEGORIES:
        navbar[category] = {
            'label': label,
            'sub_items': sub_items.filter(category=category),
        }
    return render(
        request,
        'presentation/base.html',
        {'navbar': navbar}
    )


def news_list(request, tag_slug=None):
    news_list = News.published.all()   # Отримуємо всі новини, сортуємо по даті
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        news_list = news_list.filter(tags__in=[tag])
    # Pagination with 3 news per page
    news_by = 3
    paginator = Paginator(news_list, news_by)
    page_number = request.GET.get('page', 1)
    try:
        news = paginator.page(page_number)
    except PageNotAnInteger:
        # If page_number is not an integer get the first page
        news = paginator.page(1)
    except EmptyPage:
        # If page_number is out of range get last page of results
        news = paginator.page(paginator.num_pages)

    return render(
        request,
        'presentation/news/news_list.html',
        {'news': news, 'tag': tag}
    )


def news_detail(request, year, month, day, news):
    news = get_object_or_404(
        News,
        status=News.Status.PUBLISHED,
        slug=news,
        publish__year=year,
        publish__month=month,
        publish__day=day
    )

    # List of similar posts
    news_tags_ids = news.tags.values_list('id', flat=True)
    similar_news = News.published.filter(
        tags__in=news_tags_ids
    ).exclude(id=news.id)
    similar_news = similar_news.annotate(
        same_tags=Count('tags')
    ).order_by('-same_tags', '-publish')[:4]

    return render(
        request,
        'presentation/news/news_detail.html',
        {
            'news': news,
            'similar_news': similar_news
        },
    )


def call_schedule(request):
    schedule = {
        1: [8.30, 9.15],
        2: [9.25, 10.10],
        3: [10.30, 11.15],
        4: [11.35, 12.20],
        5: [12.30, 13.15],
        6: [13.25, 14.10],
        7: [14.15, 15.00]
    }
    return render(
        request,
        'presentation/pupils_&_parents/calls_schedule.html',
        {'schedule': schedule}
    )


def lessons_schedule(request):
    clas = "8-A"
    schedule = {
        1: ["Українська мова", "с. 123 вправа 234"],
        2: ["Фізичне виховання", "форма"],
        3: ["Алгебра", "№123, 126"],
        4: ["Інформатика", "Зошит"],
        5: ["Біологія", "Зошит"],
        6: ["Хімія", "с. 134"],
        7: ["фізика", "с. 145"]
    }
    return render(
        request,
        'presentation/pupils_&_parents/lessons_schedule.html',
        {'schedule': schedule, 'clas': clas}
    )

