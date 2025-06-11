from django.db import models
from users.models import User
from django.utils import timezone


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Назва предмету")
    description = models.TextField(blank=True, verbose_name="Опис")

    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предмети"

    def __str__(self):
        return self.name


class SchoolClass(models.Model):
    # 'A', 'Б', 'В' - це letter_designation
    DoesNotExist = None
    letter_designation = models.CharField(max_length=1, verbose_name="Літерна позначка класу", default='A')
    # Рік, коли цей клас ПІШОВ В ПЕРШИЙ КЛАС.
    start_year = models.IntegerField(verbose_name="Рік початку навчання (1-й клас)", default=2010)
    # Статус класу: активний, випускний, закритий
    STATUS_CHOICES = (
        ('active', 'Активний'),
        ('graduated', 'Випускний'),  # Після 11 класу
        ('closed', 'Закритий'),  # Клас розформовано
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Статус класу")

    curator = models.OneToOneField(
        'Teacher',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="curator",
        verbose_name="Класний керівник цього класу"
    )

    class Meta:
        verbose_name = "Клас"
        verbose_name_plural = "Класи"
        # Комбінація літерної позначки та року початку навчання має бути унікальною
        unique_together = ('letter_designation', 'start_year')
        ordering = ['start_year', 'letter_designation']  # Сортування для зручності

    def __str__(self):
        return f"{self.current_grade_number()}-{self.letter_designation} (початок: {self.start_year})"

    def current_grade_number(self):
        """
        Розраховує поточний номер класу (1, 2, ..., 11)
        на основі року початку навчання та поточного навчального року.
        """
        if self.status == 'graduated':
            return 11  # Або будь-яке інше значення, яке вважається для випускного класу

        current_academic_year_start = self.get_current_academic_year_start()

        # Обчислюємо, скільки років минуло з початку навчання
        # Припускаємо, що навчальний рік починається 1 вересня.
        # Якщо поточний місяць вересень або пізніше, беремо поточний рік.
        # Якщо раніше, беремо попередній рік.

        # Різниця між поточним навчальним роком і роком початку навчання
        grade_number = current_academic_year_start - self.start_year + 1

        return grade_number

    def get_current_academic_year_start(self):
        """
        Визначає поточний календарний рік, з якого починається навчальний рік.
        Наприклад, якщо зараз травень 2025, то це навчальний рік 2024-2025 (початок 2024).
        Якщо зараз вересень 2025, то це навчальний рік 2025-2026 (початок 2025).
        """
        current_date = timezone.localdate()
        if current_date.month >= 9:  # Якщо зараз вересень або пізніше
            return current_date.year
        else:  # Якщо зараз серпень або раніше
            return current_date.year - 1

    def full_name(self):
        """Повна назва класу, наприклад '9-А'"""
        return f"{self.current_grade_number()}-{self.letter_designation}"

    @property
    def is_graduated(self):
        """Перевіряє, чи клас є випускним."""
        return self.status == 'graduated'

    @property
    def is_active(self):
        """Перевіряє, чи клас є активним."""
        return self.status == 'active'

    @property
    def is_closed(self):
        """Перевіряє, чи клас є закритим."""
        return self.status == 'closed'

    def update_status_based_on_grade(self):
        """
        Оновлює статус класу, якщо він переходить у випускний.
        Цей метод можна викликати щороку, наприклад, через Django Management Command
        або Django Signals.
        """
        if self.status == 'active' and self.current_grade_number() > 11:
            self.status = 'graduated'
            self.save()
            return True
        return False


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, verbose_name="Користувач")
    subjects = models.ManyToManyField(Subject, related_name="teachers", verbose_name="Викладає предмети")
    classes = models.ManyToManyField(SchoolClass, related_name="teachers", verbose_name="Викладає в класах") # Додано для зручності

    class Meta:
        verbose_name = "Вчитель"
        verbose_name_plural = "Вчителі"

    def __str__(self):
        return f"Вчитель: {self.user.get_full_name()}"


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, verbose_name="Користувач")
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="students",
        verbose_name="Клас"
    )

    class Meta:
        verbose_name = "Учень"
        verbose_name_plural = "Учні"

    def __str__(self):
        return f"Учень: {self.user.get_full_name()} ({self.school_class.full_name() if self.school_class else 'Немає класу'})"


class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, verbose_name="Користувач")
    children = models.ManyToManyField(Student, related_name="parents", verbose_name="Діти")

    class Meta:
        verbose_name = "Батько"
        verbose_name_plural = "Батьки"

    def __str__(self):
        return f"Батько: {self.user.get_full_name()}"