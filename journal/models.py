from django.db import models
from core.models import SchoolClass, Subject, Student, Teacher
from planning.models import LessonTopic


class Lesson(models.Model):
    lesson_topic = models.ForeignKey(LessonTopic, on_delete=models.CASCADE, verbose_name="Тема уроку за планом")
    date = models.DateField(verbose_name="Дата проведення уроку")
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name="lessons", verbose_name="Вчитель")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="lessons", verbose_name="Клас")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="lessons", verbose_name="Предмет")

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        unique_together = ('date', 'school_class', 'subject') # Один урок одного предмета в один день в одному класі
        ordering = ['-date'] # Сортування за датою від найновіших

    def __str__(self):
        return f"{self.subject.name} ({self.school_class.full_name()}) - {self.date}"


class Grade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="grades", verbose_name="Учень")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="grades", verbose_name="Урок")
    value = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 13)], verbose_name="Оцінка")

    GRADE_TYPE_CHOICES = (
        ('current', 'Поточна'),
        ('test', 'За тест'),
        ('self_study', 'За самостійну'),
        ('thematic', 'Тематична'),
        ('semester_1', 'За І семестр'),
        ('semester_2', 'За ІІ семестр'),
        ('annual', 'Річна'),
    )
    grade_type = models.CharField(max_length=20, choices=GRADE_TYPE_CHOICES, default='current', verbose_name="Тип оцінки")

    GROUP_CHOICES = (
        (1, 'Група 1'),
        (2, 'Група 2'),
        (3, 'Група 3'),
        (4, 'Група 4'),
    )
    group = models.PositiveSmallIntegerField(choices=GROUP_CHOICES, null=True, blank=True, verbose_name="Група оцінювання") # для диференційованого навчання

    comment = models.TextField(blank=True, verbose_name="Коментар")

    class Meta:
        verbose_name = "Оцінка"
        verbose_name_plural = "Оцінки"
        unique_together = ('student', 'lesson', 'grade_type') # Учень може мати лише одну оцінку певного типу за урок
        ordering = ['lesson__date', 'student__user__last_name']

    def __str__(self):
        return f"{self.student.user.get_full_name()}: {self.value} ({self.grade_type}) за {self.lesson.lesson_topic.topic} ({self.lesson.date})"


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance_records", verbose_name="Учень")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="attendance_records", verbose_name="Урок")
    is_present = models.BooleanField(default=True, verbose_name="Присутній")
    reason = models.CharField(max_length=255, blank=True, verbose_name="Причина відсутності")

    class Meta:
        verbose_name = "Відвідуваність"
        verbose_name_plural = "Відвідуваність"
        unique_together = ('student', 'lesson')
        ordering = ['lesson__date', 'student__user__last_name']

    def __str__(self):
        status = "Присутній" if self.is_present else "Відсутній"
        return f"{self.student.user.get_full_name()}: {status} на {self.lesson.lesson_topic.topic} ({self.lesson.date})"
