from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Адміністратор'),
        ('teacher', 'Вчитель'),
        ('curator', 'Класний керівник'),
        ('student', 'Учень'),
        ('parent', 'Батько'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    class Meta:
        verbose_name = 'Користувач'
        verbose_name_plural = 'Користувачі'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"

    def is_admin(self):
        return self.role == 'admin'

    def is_teacher(self):
        return self.role == 'teacher'

    def is_curator(self):
        return self.role == 'curator'

    def is_student(self):
        return self.role == 'student'

    def is_parent(self):
        return self.role == 'parent'

    @property
    def get_full_name_display(self):
        """
        Повертає повне ім'я користувача (Прізвище Ім'я По батькові).
        """
        patronymic = getattr(self.profile, 'patronymic', '') if hasattr(self, 'profile') else ''
        return f"{self.last_name or ''} {self.first_name or ''} {patronymic or ''}".strip()

    def get_initials_name(self):
        """
        Повертає ім'я у форматі: 'Прізвище І.П.'
        """
        last_name = self.last_name or ''
        initials = []

        if self.first_name:
            initials.append(self.first_name[0].upper())

        # Перевіряємо, чи існує пов'язаний об'єкт профілю
        if hasattr(self, 'profile') and self.profile.patronymic:
            patronymic = self.profile.patronymic
            initials.append(patronymic[0].upper())

        # Об'єднуємо всі частини в один рядок
        initials_str = '.'.join(initials)
        if initials_str:
            return f"{last_name} {initials_str}."
        else:
            return f"{last_name}"


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name="Користувач",
        related_name="profile"
    )
    photo = models.ImageField(
        upload_to='users_photos/',
        blank=True,
        null=True,
        verbose_name="Фото профілю"
    )
    patronymic = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="По батькові"
    )
    year_of_birth = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Рік народження"
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Додатковий опис"
    )

    # Поля, специфічні для учнів
    admission_year = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Рік вступу до навчального закладу"
    )

    # Поля, специфічні для вчителів / класних керівників
    start_work_year = models.IntegerField(
        blank=True,
        null=True,
        verbose_name="Рік початку роботи"
    )
    position = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Посада"
    )
    achievements = models.TextField(
        blank=True,
        null=True,
        verbose_name="Досягнення"
    )

    class Meta:
        verbose_name = "Профіль користувача"
        verbose_name_plural = "Профілі користувачів"

    def __str__(self):
        return f"Профіль {self.user.username}"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
