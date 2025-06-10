from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
import logging

from users.decorators import teacher_required  # Імпортуємо наш декоратор
from core.models import SchoolClass, Subject, Student, Teacher
from journal.models import Lesson, Grade, Attendance
from planning.models import LessonTopic, CurriculumPlan

from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect


logger = logging.getLogger(__name__)


@login_required
@teacher_required
def teacher_dashboard(request):
    """Панель вчителя: список класів та предметів, які він викладає."""
    user_teacher = request.user.teacher

    teaching_classes = user_teacher.classes.all().order_by('start_year', 'letter_designation')
    teaching_subjects = user_teacher.subjects.all().order_by('name')

    try:
        curator = user_teacher.curator
    except SchoolClass.DoesNotExist:
        curator = None

    context = {
        'teacher': user_teacher,
        'teaching_classes': teaching_classes,
        'teaching_subjects': teaching_subjects,
        'curator': curator,
    }
    return render(request, 'frontend/teacher/dashboard.html', context)


@login_required
@teacher_required
def teacher_journal(request, class_id, subject_id):
    """
    Сторінка журналу оцінок для вчителя по календарних днях.
    """
    user_teacher = request.user.teacher
    school_class = get_object_or_404(SchoolClass, id=class_id)
    subject = get_object_or_404(Subject, id=subject_id)

    # Перевірка дозволів: вчитель повинен викладати цей предмет у цьому класі
    if not user_teacher.classes.filter(id=school_class.id).exists() or \
            not user_teacher.subjects.filter(id=subject.id).exists():
        messages.error(request, "У вас немає дозволу переглядати цей журнал.")
        return redirect('teacher_dashboard')

    # Визначення періоду для журналу (наприклад, поточний місяць або семестр)
    today = timezone.localdate()
    start_date = today.replace(day=1)  # Початок місяця
    end_date = start_date + timedelta(days=30)  # Кінець місяця (приблизно)

    # Фільтрація уроків для даного класу, предмету та вчителя за період
    lessons = Lesson.objects.filter(
        school_class=school_class,
        subject=subject,
        teacher=user_teacher,
        date__gte=start_date,
        date__lte=end_date
    ).select_related('lesson_topic').order_by('date')

    students = Student.objects.filter(school_class=school_class).order_by('user__last_name', 'user__first_name')

    # Збираємо дані для таблиці журналу
    # grade_data = { (student_id, lesson_date): grade_value, ... }
    # attendance_data = { (student_id, lesson_date): is_present, ... }
    grades_by_student_lesson = defaultdict(lambda: defaultdict(dict))
    attendance_by_student_lesson = defaultdict(lambda: defaultdict(dict))

    logger.debug(f"Initial grades_by_student_lesson type: {type(grades_by_student_lesson)}")
    logger.debug(f"Initial grades_by_student_lesson default_factory: {grades_by_student_lesson.default_factory}")

    all_grades = Grade.objects.filter(
        student__in=students,
        lesson__in=lessons
    ).select_related('student', 'lesson')

    all_attendance = Attendance.objects.filter(
        student__in=students,
        lesson__in=lessons
    ).select_related('student', 'lesson')

    for grade in all_grades:
        grades_by_student_lesson[grade.student.pk][grade.lesson.pk][grade.grade_type] = {  # Використовуємо .pk
            'value': grade.value,
            'id': grade.id,
            'group': grade.group,
            'comment': grade.comment
        }
    logger.debug(f"Final grades_by_student_lesson: {grades_by_student_lesson!r}")

    for attendance in all_attendance:
        student_pk = grade.student.pk
        lesson_id = grade.lesson.id
        grade_type = grade.grade_type

        # Додайте ці рядки для відлагодження всередині циклу
        logger.debug(f"Processing grade for student_pk={student_pk}, lesson_id={lesson_id}, grade_type={grade_type}")
        # Перевіряємо тип об'єкта, який повертає перший рівень defaultdict
        current_student_dict = grades_by_student_lesson[student_pk]
        logger.debug(f"grades_by_student_lesson[{student_pk}] type: {type(current_student_dict)}")
        # Перевіряємо тип об'єкта, який повертає другий рівень defaultdict
        current_lesson_dict = current_student_dict[lesson_id]
        logger.debug(f"grades_by_student_lesson[{student_pk}][{lesson_id}] type: {type(current_lesson_dict)}")
        # Зберігаємо дані відвідуваності напряму
        attendance_by_student_lesson[attendance.student.pk][attendance.lesson.pk] = {  # Використовуємо .pk
            'is_present': attendance.is_present,
            'id': attendance.id,
            'reason': attendance.reason
        }
    logger.debug(f"Final attendance_by_student_lesson: {attendance_by_student_lesson!r}")

    # Для відображення типів оцінок та груп
    grade_types_choices = Grade.GRADE_TYPE_CHOICES
    group_choices = Grade.GROUP_CHOICES

    logger.debug(f"Final grades_by_student_lesson: {grades_by_student_lesson}")

    context = {
        'school_class': school_class,
        'subject': subject,
        'teacher': user_teacher,
        'students': students,
        'lessons': lessons,
        'grades_by_student_lesson': grades_by_student_lesson,
        'attendance_by_student_lesson': attendance_by_student_lesson,
        'start_date': start_date,
        'end_date': end_date,
        'grade_types_choices': grade_types_choices,
        'group_choices': group_choices,
        'current_grade_type': 'current',
    }
    return render(request, 'frontend/teacher/journal.html', context)


@login_required
@teacher_required
@require_POST  # Дозволяємо лише POST-запити
@csrf_protect  # Захист від CSRF
def update_grade(request):
    """
    Обробляє AJAX-запити на створення/оновлення/видалення оцінки.
    """
    student_id = request.POST.get('student_id')
    lesson_id = request.POST.get('lesson_id')
    grade_value = request.POST.get('grade_value')  # string, може бути порожнім
    grade_type = request.POST.get('grade_type', 'current')
    group = request.POST.get('group')
    grade_id = request.POST.get('grade_id')  # ID існуючої оцінки, якщо оновлюємо

    try:
        student = get_object_or_404(Student, user__id=student_id)
        lesson = get_object_or_404(Lesson, id=lesson_id)

        # Перевірка дозволів: вчитель може редагувати оцінки лише для своїх уроків
        if lesson.teacher.user != request.user:
            return JsonResponse({'status': 'error', 'message': 'Недостатньо прав для редагування цієї оцінки.'},
                                status=403)

        if grade_value:
            # Перевірка на число та діапазон
            try:
                grade_value = int(grade_value)
                if not (1 <= grade_value <= 12):
                    raise ValueError("Оцінка повинна бути від 1 до 12.")
            except (ValueError, TypeError):
                return JsonResponse(
                    {'status': 'error', 'message': 'Некоректне значення оцінки. Введіть число від 1 до 12.'},
                    status=400)

            # Якщо grade_id є, намагаємося оновити існуючу оцінку
            if grade_id:
                grade = get_object_or_404(Grade, id=grade_id, student=student, lesson=lesson)
                grade.value = grade_value
                grade.grade_type = grade_type
                grade.group = int(group) if group else None  # Convert to int or None
                grade.save()
            else:
                # Створюємо нову оцінку
                grade = Grade.objects.create(
                    student=student,
                    lesson=lesson,
                    value=grade_value,
                    grade_type=grade_type,
                    group=int(group) if group else None
                )
            return JsonResponse({'status': 'success', 'message': 'Оцінку збережено.', 'grade_id': grade.id})
        else:  # Якщо grade_value порожнє, значить оцінку видаляють
            if grade_id:
                grade = get_object_or_404(Grade, id=grade_id, student=student, lesson=lesson)
                grade.delete()
                return JsonResponse({'status': 'success', 'message': 'Оцінку видалено.', 'grade_id': None})
            else:
                return JsonResponse({'status': 'error', 'message': 'Немає оцінки для збереження або видалення.'},
                                    status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@teacher_required
@require_POST
@csrf_protect
def update_attendance(request):
    """
    Обробляє AJAX-запити на створення/оновлення відвідуваності.
    """
    student_id = request.POST.get('student_id')
    lesson_id = request.POST.get('lesson_id')
    is_present = request.POST.get('is_present') == 'true'  # Чекбокс повертає 'true' або нічого
    reason = request.POST.get('reason', '').strip()
    attendance_id = request.POST.get('attendance_id')

    try:
        student = get_object_or_404(Student, id=student_id)
        lesson = get_object_or_404(Lesson, id=lesson_id)

        # Перевірка дозволів
        if lesson.teacher.user != request.user:
            return JsonResponse({'status': 'error', 'message': 'Недостатньо прав для редагування відвідуваності.'},
                                status=403)

        if attendance_id:
            attendance = get_object_or_404(Attendance, id=attendance_id, student=student, lesson=lesson)
            attendance.is_present = is_present
            attendance.reason = reason if not is_present else ''  # Причина лише якщо відсутній
            attendance.save()
        else:
            attendance = Attendance.objects.create(
                student=student,
                lesson=lesson,
                is_present=is_present,
                reason=reason if not is_present else ''
            )
        return JsonResponse(
            {'status': 'success', 'message': 'Відвідуваність збережено.', 'attendance_id': attendance.id})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)