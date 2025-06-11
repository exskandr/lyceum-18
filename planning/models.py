from django.db import models
from core.models import SchoolClass, Subject, Teacher


class CurriculumPlan(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="curriculum_plans", verbose_name="Вчитель")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="curriculum_plans", verbose_name="Клас")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="curriculum_plans", verbose_name="Предмет")
    academic_year = models.IntegerField(verbose_name="Навчальний рік")
    # Тут можна додати поля для загального опису плану, наприклад, "Програма курсу"

    class Meta:
        verbose_name = "Календарний план"
        verbose_name_plural = "Календарні плани"
        unique_together = ('teacher', 'school_class', 'subject', 'academic_year')

    def __str__(self):
        return f"План: {self.subject.name} для {self.school_class.full_name()} ({self.academic_year}) - {self.teacher.user.get_full_name()}"


class LessonTopic(models.Model):
    plan = models.ForeignKey(CurriculumPlan, on_delete=models.CASCADE, related_name="lesson_topics", verbose_name="Календарний план")
    lesson_number = models.IntegerField(verbose_name="Номер уроку")
    topic = models.CharField(max_length=255, verbose_name="Тема уроку")
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
            (None, 'Немає групи'), # Додаємо варіант None для відсутності групи
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
        unique_together = ('plan', 'lesson_number') # Унікальний номер уроку в межах плану
        ordering = ['lesson_number']

    def __str__(self):
        group_display = f" (гр. оц. {self.group})" if self.group is not None else ""
        return f"Урок {self.lesson_number} {group_display}: " \
               f"{self.topic}  ({self.plan.subject.name} - {self.plan.school_class.full_name()})"
