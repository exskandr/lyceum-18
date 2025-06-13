# planning/models.py
from django.db import models
from core.models import SchoolClass, Subject, Teacher


# Допоміжна модель для днів тижня (залишається без змін)
class LessonDay(models.Model):
    DAY_CHOICES = [
        ('MON', 'Понеділок'), ('TUE', 'Вівторок'), ('WED', 'Середа'),
        ('THU', 'Четвер'), ('FRI', 'П\'ятниця'), ('SAT', 'Субота'), ('SUN', 'Неділя')
    ]
    name = models.CharField(max_length=3, choices=DAY_CHOICES, unique=True,
                            verbose_name="День тижня")

    def __str__(self):
        return self.get_name_display()

    class Meta:
        verbose_name = "День проведення уроку"
        verbose_name_plural = "Дні проведення уроків"
        ordering = ['id']


class CurriculumPlan(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="curriculum_plans", verbose_name="Вчитель")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="curriculum_plans", verbose_name="Клас")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="curriculum_plans", verbose_name="Предмет")
    academic_year = models.IntegerField(verbose_name="Навчальний рік")
    academic_year_start = models.DateField(null=True, blank=True, verbose_name="Початок навчального року")
    academic_year_end = models.DateField(null=True, blank=True, verbose_name="Кінець навчального року")

    semester_1_start = models.DateField(null=True, blank=True, verbose_name="Початок І семестру")
    semester_1_end = models.DateField(null=True, blank=True, verbose_name="Кінець І семестру")
    semester_2_start = models.DateField(null=True, blank=True, verbose_name="Початок ІІ семестру")
    semester_2_end = models.DateField(null=True, blank=True, verbose_name="Кінець ІІ семестру")

    lesson_frequency_days = models.ManyToManyField(LessonDay, blank=True, verbose_name="Дні проведення уроків")

    vacation_periods_json = models.JSONField(blank=True, null=True, verbose_name="Періоди канікул")

    class Meta:
        verbose_name = "Календарний план"
        verbose_name_plural = "Календарні плани"
        unique_together = ('teacher', 'school_class', 'subject', 'academic_year')

    def __str__(self):
        return f"План для {self.school_class.full_name()} - {self.subject.name} ({self.academic_year})"


# НОВА МОДЕЛЬ: Навчальна тема (розділ)
class CurriculumUnit(models.Model):
    plan = models.ForeignKey(CurriculumPlan, on_delete=models.CASCADE, related_name="curriculum_units", verbose_name="Календарний план")
    title = models.CharField(max_length=255, verbose_name="Назва навчальної теми (розділу)")
    order = models.IntegerField(verbose_name="Порядок теми в плані") # Для сортування розділів

    class Meta:
        verbose_name = "Навчальна тема (розділ)"
        verbose_name_plural = "Навчальні теми (розділи)"
        unique_together = ('plan', 'order') # Кожен план має унікальний порядок тем
        ordering = ['order']

    def __str__(self):
        # Змінено для кращого відображення, наприклад: "[Математика] 1. Квадратні рівняння"
        return f"[{self.plan.subject.name}] {self.order}. {self.title}"


class LessonTopic(models.Model):
    plan = models.ForeignKey(CurriculumPlan, on_delete=models.CASCADE, related_name="lesson_topics", verbose_name="Календарний план")
    # НОВЕ ПОЛЕ: Зв'язок з CurriculumUnit
    # SET_NULL дозволяє зберегти LessonTopic, навіть якщо CurriculumUnit видалено (хоча це не рекомендовано)
    # Null=True, blank=True, оскільки не кожен урок обов'язково належить до великої теми
    curriculum_unit = models.ForeignKey(CurriculumUnit, on_delete=models.SET_NULL, null=True, blank=True,
                                        related_name="lesson_topics_in_unit", verbose_name="Навчальна тема (розділ)")
    lesson_number = models.IntegerField(verbose_name="Номер уроку")
    topic = models.CharField(max_length=255, verbose_name="Тема уроку") # Це тепер "тема конкретного уроку"
    homework = models.TextField(blank=True, verbose_name="Домашнє завдання")

    LESSON_TYPE_CHOICES = (
        ('lecture', 'Лекція'),
        ('practice', 'Практична робота'),
        ('self_study', 'Самостійна робота'),
        ('test', 'Тестова робота'),
        ('control', 'Контрольна робота'),
        ('other', 'Інше'),
    )
    lesson_type = models.CharField(max_length=20,
                                   choices=LESSON_TYPE_CHOICES,
                                   default='lecture',
                                   verbose_name="Тип уроку")

    GROUP_CHOICES = (
            (None, 'Немає групи'),
            (1, 'Група 1'),
            (2, 'Група 2'),
            (3, 'Група 3'),
            (4, 'Група 4'),
        )
    group = models.IntegerField(choices=GROUP_CHOICES,
                                null=True,
                                blank=True,
                                verbose_name="Група оцінювання")

    class Meta:
        verbose_name = "Тема уроку"
        verbose_name_plural = "Теми уроків"
        unique_together = ('plan', 'lesson_number')
        ordering = ['lesson_number']

    def __str__(self):
        group_display = f" (гр. оц. {self.group})" if self.group is not None else ""
        # Додаємо відображення назви CurriculumUnit, якщо вона є
        unit_display = f" [{self.curriculum_unit.title}]" if self.curriculum_unit else ""
        return f"Урок {self.lesson_number}{group_display}: " \
               f"{self.topic}{unit_display}  ({self.plan.subject.name} - {self.plan.school_class.full_name()})"