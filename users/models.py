from django.contrib.auth.models import AbstractUser
from django.db import models


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
