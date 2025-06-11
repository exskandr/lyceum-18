# journal/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict
import logging

from users.decorators import teacher_required
from core.models import SchoolClass, Subject, Student
from journal.models import Lesson, Grade, Attendance
from planning.models import LessonTopic

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
    end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(days=1) # Останній день поточного місяця

    # Фільтрація уроків для даного класу, предмету та вчителя за період
    lessons = Lesson.objects.filter(
        school_class=school_class,
        subject=subject,
        teacher=user_teacher,
        date__gte=start_date,
        date__lte=end_date
    ).select_related('lesson_topic').order_by('date')

    students = Student.objects.filter(school_class=school_class).order_by('user__last_name', 'user__first_name')

    current_grade_types_keys = [t[0] for t in Grade.CURRENT_GRADE_TYPES]

    grades_by_student_lesson = defaultdict(dict)
    attendance_by_student_lesson = defaultdict(dict)

    lesson_topics_data = {} # Зберігатиме інформацію про тему уроку, включаючи групу

    # Отримуємо всі поточні оцінки за раз
    all_grades = Grade.objects.filter(
        student__in=students,
        lesson__in=lessons,
        grade_type__in=current_grade_types_keys
    ).select_related('student__user', 'lesson__lesson_topic')

    for grade in all_grades:
        grades_by_student_lesson[grade.student.pk][grade.lesson.pk] = {
            'value': grade.value,
            'id': grade.id,
            'comment': grade.comment,
            'grade_type': grade.grade_type,
            'grade_type_display': dict(Grade.GRADE_TYPE_CHOICES).get(grade.grade_type, grade.grade_type)
        }
    logger.debug(f"Final grades_by_student_lesson: {grades_by_student_lesson!r}")

    # Отримуємо всі записи відвідуваності за раз
    all_attendance = Attendance.objects.filter(
        student__in=students,
        lesson__in=lessons,
    ).select_related('student__user', 'lesson__lesson_topic')

    for attendance in all_attendance:
        attendance_by_student_lesson[attendance.student.pk][attendance.lesson.pk] = {
            'id': attendance.id,
            'is_present': attendance.is_present,
            'reason': attendance.reason,
        }
    logger.debug(f"Final attendance_by_student_lesson: {attendance_by_student_lesson!r}")

    # Збираємо інформацію про LessonTopic для JavaScript
    for lesson in lessons:
        lesson_topics_data[lesson.id] = {
            'topic': lesson.lesson_topic.topic,
            'homework': lesson.lesson_topic.homework,
            'group': lesson.lesson_topic.group if lesson.lesson_topic.group is not None else None,
            'topic_display': lesson.lesson_topic.topic
        }

    grade_types_choices = list(Grade.CURRENT_GRADE_TYPES)
    group_choices = list(LessonTopic.GROUP_CHOICES)

    context = {
        'school_class': school_class,
        'subject': subject,
        'teacher': user_teacher,
        'students': students,
        'lessons': lessons,
        'grades_by_student_lesson': grades_by_student_lesson,
        'attendance_by_student_lesson': attendance_by_student_lesson,
        'lesson_topics_data': lesson_topics_data,
        'start_date': start_date,
        'end_date': end_date,
        'grade_types_choices': grade_types_choices,
        'group_choices': group_choices,
    }
    return render(request, 'frontend/teacher/journal.html', context)


@login_required
@teacher_required
@require_POST
@csrf_protect
def update_grade(request):
    """
    Обробляє AJAX-запити на створення/оновлення/видалення оцінки.
    """
    student_id = request.POST.get('student_id')
    lesson_id = request.POST.get('lesson_id')
    grade_value = request.POST.get('grade_value')
    grade_type = request.POST.get('grade_type', 'current')
    grade_id = request.POST.get('grade_id')

    try:
        student = get_object_or_404(Student, user__id=student_id)
        lesson = get_object_or_404(Lesson, id=lesson_id)

        # Перевірка дозволів
        if lesson.teacher.user != request.user:
            return JsonResponse({'status': 'error', 'message': 'Недостатньо прав для редагування цієї оцінки.'},
                                status=403)

        if grade_value:
            try:
                grade_value = int(grade_value)
                if not (1 <= grade_value <= 12):
                    raise ValueError("Оцінка повинна бути від 1 до 12.")
            except (ValueError, TypeError):
                return JsonResponse(
                    {'status': 'error', 'message': 'Некоректне значення оцінки. Введіть число від 1 до 12.'},
                    status=400)

            # Намагаємося знайти існуючу оцінку за student та lesson (без group)
            grade_obj, created = Grade.objects.get_or_create(
                student=student,
                lesson=lesson,
                defaults={'value': grade_value, 'grade_type': grade_type}
            )

            if not created: # Якщо оцінка вже існувала, оновлюємо її
                grade_obj.value = grade_value
                grade_obj.grade_type = grade_type # Може бути змінено
                grade_obj.save()

            # Повертаємо повні дані для оновлення на фронтенді
            return JsonResponse({
                'status': 'success',
                'message': 'Оцінку збережено.',
                'grade_id': grade_obj.id,
                'grade_value': grade_obj.value,
                'grade_type': grade_obj.grade_type,
                'grade_type_display': dict(Grade.GRADE_TYPE_CHOICES).get(grade_obj.grade_type, grade_obj.grade_type),
                'group': lesson.lesson_topic.group if lesson.lesson_topic.group is not None else None # Тепер група повертається з lesson_topic, а не з grade
            })
        else:  # Якщо grade_value порожнє, значить оцінку видаляють
            if grade_id:
                # Шукаємо оцінку за ID, а також за student та lesson для безпеки
                grade_obj = get_object_or_404(Grade, id=grade_id, student=student, lesson=lesson)
                grade_obj.delete()
                # Повертаємо дані для "порожньої" клітинки
                return JsonResponse({
                    'status': 'success',
                    'message': 'Оцінку видалено.',
                    'grade_id': None,
                    'grade_value': None,
                    'grade_type': None,
                    'group': lesson.lesson_topic.group if lesson.lesson_topic.group is not None else None # Повертаємо групу уроку
                })
            else:
                return JsonResponse({'status': 'error', 'message': 'Немає оцінки для збереження або видалення.'},
                                    status=400)

    except Exception as e:
        logger.error(f"Error updating grade: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': f"Помилка при збереженні оцінки: {e}"}, status=500)


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
    is_present = request.POST.get('is_present') == 'true'
    reason = request.POST.get('reason', '').strip()
    attendance_id = request.POST.get('attendance_id')

    try:
        student = get_object_or_404(Student, user__id=student_id)
        lesson = get_object_or_404(Lesson, id=lesson_id)

        # Перевірка дозволів
        if lesson.teacher.user != request.user:
            return JsonResponse({'status': 'error', 'message': 'Недостатньо прав для редагування відвідуваності.'},
                                status=403)

        if attendance_id:
            attendance_obj = get_object_or_404(Attendance, id=attendance_id, student=student, lesson=lesson)
            attendance_obj.is_present = is_present
            attendance_obj.reason = reason if not is_present else ''
            attendance_obj.save()
        else:
            if is_present and not reason:
                existing_attendance = Attendance.objects.filter(student=student, lesson=lesson).first()
                if existing_attendance:
                    existing_attendance.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Відвідуваність встановлено як "Присутній".',
                    'attendance_id': None,
                    'is_present': True,
                    'reason': ''
                })
            else:
                attendance_obj = Attendance.objects.create(
                    student=student,
                    lesson=lesson,
                    is_present=is_present,
                    reason=reason if not is_present else ''
                )

        return JsonResponse({
            'status': 'success',
            'message': 'Відвідуваність збережено.',
            'attendance_id': attendance_obj.id if attendance_obj else None,
            'is_present': is_present,
            'reason': reason if not is_present else ''
        })

    except Exception as e:
        logger.error(f"Error updating attendance: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': f"Помилка при збереженні відвідуваності: {e}"}, status=500)