from taggit.managers import TaggableManager
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils import timezone


class DynamicPage(models.Model):
    title = models.CharField(max_length=200)  # Назва сторінки
    slug = models.SlugField(unique=True)  # URL-ідентифікатор сторінки
    content = models.TextField()  # Контент сторінки (HTML або текст)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f"/pages/{self.slug}/"


class NavbarSubItem(models.Model):
    MAIN_CATEGORIES = [
        ('NEWS&BLOGS', 'News & Blogs'),
        ('PUPILS&PARENTS', 'Pupils & Parents'),
        ('ACTIVITY', 'Activity'),
        ('HOME', 'Home'),
        ('OUR_SCHOOL', 'Our School'),
        ('ABOUT', 'About'),
        ('CONTACT', 'Contact'),
    ]

    category = models.CharField(max_length=50, choices=MAIN_CATEGORIES)
    name = models.CharField(max_length=100)
    url = models.CharField(max_length=200, blank=True)  # URL для підкатегорії
    dynamic_page = models.ForeignKey('DynamicPage', on_delete=models.SET_NULL, null=True, blank=True)  # Посилання на сторінку
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.category} - {self.name}"

    class Meta:
        ordering = ['category', 'order']


class PublishedManager(models.Manager):
    def get_queryset(self):
        return (
            super().get_queryset().filter(status=News.Status.PUBLISHED)
        )


class News(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DF', 'Draft'
        PUBLISHED = 'PB', 'Published'

    title = models.CharField(max_length=200)  # Заголовок новини
    slug = models.SlugField(max_length=250, unique_for_date='publish')
    main_image = models.ImageField(upload_to='news_main_images/')  # Головне фото
    content = models.TextField()  # Текст новини
    photos = models.ManyToManyField('Photo', blank=True)  # Додаткові фотографії
    videos = models.ManyToManyField('Video', blank=True)  # Відео
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)  # Автор новини
    publish = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=2,
        choices=Status,
        default=Status.DRAFT
    )
    objects = models.Manager()      # The default manager.
    published = PublishedManager()  # Our custom manager.
    tags = TaggableManager()

    class Meta:
        ordering = ['-publish']
        indexes = [
            models.Index(fields=['-publish']),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            'news:news_detail',
            args=[self.publish.year,
                  self.publish.month,
                  self.publish.day,
                  self.slug
                  ]
        )


class Photo(models.Model):
    image = models.ImageField(upload_to='news_photos/')
    description = models.CharField(max_length=200, blank=True)
    tags = TaggableManager()

    def __str__(self):
        return f"Photo {self.id}"


class Video(models.Model):
    video_url = models.URLField()  # Посилання на відео (YouTube або інші)
    description = models.CharField(max_length=200, blank=True)
    tags = TaggableManager()

    def __str__(self):
        return f"Video {self.id}"
