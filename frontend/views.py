# journal/views.py
import json
import calendar
import logging

from django.urls import reverse

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, date, datetime
from collections import defaultdict


from users.decorators import teacher_required
from core.models import SchoolClass, Subject, Student, Teacher
from journal.models import Lesson, Grade, Attendance
from planning.models import LessonTopic,  CurriculumPlan, LessonDay

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


@login_required
@teacher_required
def teacher_planning_settings_view(request, class_id, subject_id):
    user_teacher = request.user.teacher
    school_class = get_object_or_404(SchoolClass, id=class_id)
    subject = get_object_or_404(Subject, id=subject_id)

    # Визначення поточного навчального року для дефолту
    current_year = date.today().year
    if date.today().month >= 9:  # Якщо зараз вересень або пізніше, навчальний рік починається з поточного року
        academic_year_default = current_year
    else:  # Якщо до вересня, навчальний рік починається з попереднього року
        academic_year_default = current_year - 1

    curriculum_plan, created = CurriculumPlan.objects.get_or_create(
        school_class=school_class,
        subject=subject,
        teacher=user_teacher,
        academic_year=academic_year_default,  # Додаємо academic_year до get_or_create
        defaults={
            'academic_year_start': date(academic_year_default, 9, 1),
            'academic_year_end': date(academic_year_default + 1, 5, 31)
        }
    )

    lesson_days = LessonDay.objects.all().order_by('id')  # Забезпечуємо порядок Пн, Вт...

    # Створюємо ОДИН об'єкт js_data для передачі всіх необхідних даних
    js_data = {
        'class_id': school_class.id,
        'subject_id': subject.id,
        # Замість хардкодженних URL, використовуємо reverse для динамічного створення URL
        # Передаємо 0 як заглушку, яку потім замінить JavaScript
        'generate_lessons_url_template': reverse('generate_lessons_for_plan', args=[0, 0]),
        'save_plan_and_lessons_url_template': reverse('save_plan_and_lessons', args=[0, 0]),
        'python_days_of_week_map': {
            'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6
        },
        'lesson_type_choices': list(LessonTopic.LESSON_TYPE_CHOICES),  # Конвертуємо у список для JSON
        'group_choices': list(LessonTopic.GROUP_CHOICES),  # Конвертуємо у список для JSON
        'academic_year_for_plan': curriculum_plan.academic_year,
    }

    context = {
        'school_class': school_class,
        'subject': subject,
        'teacher': user_teacher,
        'curriculum_plan': curriculum_plan,
        'lesson_days': lesson_days,  # Це для HTML-розмітки, де ви генеруєте чекбокси
        'js_data': js_data,  # Передаємо єдиний об'єкт js_data в контекст
    }
    return render(request, 'frontend/teacher/planning_settings.html', context)


@login_required
@teacher_required
def teacher_curriculum_detail_view(request, class_id, subject_id):
    user_teacher = request.user.teacher
    school_class = get_object_or_404(SchoolClass, id=class_id)
    subject = get_object_or_404(Subject, id=subject_id)

    # Визначення поточного навчального року для отримання плану
    current_year = date.today().year
    if date.today().month >= 9:
        academic_year_filter = current_year
    else:
        academic_year_filter = current_year - 1

    curriculum_plan = get_object_or_404(CurriculumPlan,
                                        school_class=school_class,
                                        subject=subject,
                                        teacher=user_teacher,
                                        academic_year=academic_year_filter
                                        )

    # Завантажуємо всі LessonTopic, що належать цьому плану
    planned_lesson_topics = curriculum_plan.lesson_topics.all().order_by('lesson_number')

    lesson_dates_by_topic_number = {}

    # Оптимізований спосіб:
    lesson_topics_ids = [lt.id for lt in planned_lesson_topics]
    lessons_from_db = Lesson.objects.filter(
        lesson_topic__id__in=lesson_topics_ids,
        school_class=school_class,
        subject=subject,
        teacher=user_teacher
    ).select_related('lesson_topic')  # Завантажуємо пов'язаний LessonTopic для оптимізації

    # Створюємо словник: { lesson_number: date_string }
    for lesson_obj in lessons_from_db:
        if lesson_obj.lesson_topic and lesson_obj.lesson_topic.plan == curriculum_plan:  # Додаткова перевірка
            lesson_dates_by_topic_number[str(lesson_obj.lesson_topic.lesson_number)] = lesson_obj.date.isoformat()

    context = {
        'school_class': school_class,
        'subject': subject,
        'teacher': user_teacher,
        'curriculum_plan': curriculum_plan,
        'planned_lessons': planned_lesson_topics,  # Передаємо існуючі LessonTopic
        'lesson_type_choices': LessonTopic.LESSON_TYPE_CHOICES,
        'group_choices': LessonTopic.GROUP_CHOICES,
        'lesson_dates_by_topic_number': lesson_dates_by_topic_number,  # Нове поле для JS
    }
    return render(request, 'frontend/teacher/planning_detail.html', context)


@login_required
@teacher_required
@require_POST
@csrf_protect
def generate_lessons_for_plan(request, class_id, subject_id):
    user_teacher = request.user.teacher
    school_class = get_object_or_404(SchoolClass, id=class_id)
    subject = get_object_or_404(Subject, id=subject_id)

    # Валідація дозволів
    if not user_teacher.classes.filter(id=school_class.id).exists() or \
            not user_teacher.subjects.filter(id=subject.id).exists():
        return JsonResponse({'status': 'error', 'message': 'Недостатньо прав.'}, status=403)

    try:
        # Отримуємо дані з POST-запиту
        academic_year_start_str = request.POST.get('academic_year_start')
        academic_year_end_str = request.POST.get('academic_year_end')
        selected_days_str = request.POST.getlist('lesson_frequency_days[]')
        vacation_periods_json_str = request.POST.get('vacation_periods_json')

        plan_start = date.fromisoformat(academic_year_start_str)
        plan_end = date.fromisoformat(academic_year_end_str)

        # Перетворення днів тижня з назв на числа (0=Понеділок, 6=Неділя)
        day_map = {
            'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6
        }
        days_to_include_weekdays = [day_map[day] for day in selected_days_str if day in day_map]

        vacation_periods = []
        if vacation_periods_json_str:
            vacations_data = json.loads(vacation_periods_json_str)
            for period in vacations_data:
                vacation_periods.append({
                    'start': date.fromisoformat(period['start']),
                    'end': date.fromisoformat(period['end'])
                })

        generated_lessons_data = []
        current_date = plan_start
        lesson_number = 1

        while current_date <= plan_end:
            if current_date.weekday() in days_to_include_weekdays:
                is_vacation = False
                for vac_period in vacation_periods:
                    if vac_period['start'] <= current_date <= vac_period['end']:
                        is_vacation = True
                        break

                if not is_vacation:
                    generated_lessons_data.append({
                        'lesson_number': lesson_number,
                        'date': current_date.isoformat(),
                        'topic': f'Урок {lesson_number}',
                        'homework': '',
                        'lesson_type': 'lecture',
                        'group': None,
                    })
                    lesson_number += 1
            current_date += timedelta(days=1)

        return JsonResponse({'status': 'success', 'lessons': generated_lessons_data})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'status': 'error', 'message': f"Помилка генерації плану: {e}"}, status=500)


@login_required
@teacher_required
@require_POST
@csrf_protect
def save_plan_and_lessons(request, class_id, subject_id):
    user_teacher = request.user.teacher
    school_class = get_object_or_404(SchoolClass, id=class_id)
    subject = get_object_or_404(Subject, id=subject_id)

    if not user_teacher.classes.filter(id=school_class.id).exists() or \
            not user_teacher.subjects.filter(id=subject.id).exists():
        return JsonResponse({'status': 'error', 'message': 'Недостатньо прав.'}, status=403)

    try:
        data = json.loads(request.body)
        logger.info(f"Отримані ключі у JSON-запиті: {data.keys()}")

        # Оновлення CurriculumPlan (налаштування плану)
        academic_year_val = int(data.get('academic_year'))
        if academic_year_val is None:
            academic_year_start_str = data.get('academic_year_start')
            if academic_year_start_str:
                academic_year_val = datetime.strptime(academic_year_start_str, '%Y-%m-%d').year
            else:
                # Це буде рідкісна ситуація, але важливо обробити
                raise ValueError("Academic year or academic year start date is missing.")
        else:
            academic_year_val = int(academic_year_val)  # Переконаємось, що це ціле число
        curriculum_plan, created = CurriculumPlan.objects.get_or_create(
            school_class=school_class,
            subject=subject,
            teacher=user_teacher,
            academic_year=academic_year_val,
            defaults={
                'academic_year_start': date.fromisoformat(data['academic_year_start']),
                'academic_year_end': date.fromisoformat(data['academic_year_end']),
            }
        )

        curriculum_plan.academic_year_start = date.fromisoformat(data['academic_year_start'])
        curriculum_plan.academic_year_end = date.fromisoformat(data['academic_year_end'])
        curriculum_plan.semester_1_start = date.fromisoformat(data['semester_1_start']) if data.get(
            'semester_1_start') else None
        curriculum_plan.semester_1_end = date.fromisoformat(data['semester_1_end']) if data.get(
            'semester_1_end') else None
        curriculum_plan.semester_2_start = date.fromisoformat(data['semester_2_start']) if data.get(
            'semester_2_start') else None
        curriculum_plan.semester_2_end = date.fromisoformat(data['semester_2_end']) if data.get(
            'semester_2_end') else None
        curriculum_plan.vacation_periods_json = json.loads(data['vacation_periods_json']) if data.get(
            'vacation_periods_json') else None

        # Оновлення M2M поля LessonDay
        curriculum_plan.lesson_frequency_days.clear()
        for day_name in data.get('lesson_frequency_days', []):
            day_obj = LessonDay.objects.get(name=day_name)
            curriculum_plan.lesson_frequency_days.add(day_obj)

        curriculum_plan.save()

        curriculum_plan.lesson_topics.all().delete()

        Lesson.objects.filter(
            school_class=school_class,
            subject=subject,
            teacher=user_teacher,
            lesson_topic__plan=curriculum_plan  # Фільтруємо за планом
        ).delete()

        # Збереження/оновлення LessonTopic об'єктів
        lessons_data_from_form = data.get('lessons', [])
        logger.info(f"Кількість уроків (lessons) отриманих з фронтенду: {len(lessons_data_from_form)}")
        if len(lessons_data_from_form) > 0:
            # Якщо є уроки, залогіть перші кілька для перевірки формату
            logger.debug(f"Приклад першого уроку з отриманих: {lessons_data_from_form[0]}")
        else:
            logger.warning("Список 'lessons' у запиті від фронтенду порожній.")  # <--- ЦЕЙ ЛОГ ДУЖЕ ВАЖЛИВИЙ
        created_lessons_count = 0  # Будемо рахувати фактично створені Lesson об'єкти
        for lesson_item in lessons_data_from_form:
            lesson_number = lesson_item['lesson_number']
            topic_text = lesson_item['topic'].strip()
            homework = lesson_item['homework'].strip()
            lesson_type = lesson_item['lesson_type']
            group = int(lesson_item['group']) if lesson_item['group'] is not None and lesson_item[
                'group'] != '' else None

            if not topic_text:
                continue  # Пропускаємо уроки без теми

            # Створюємо новий LessonTopic для цього плану
            lesson_topic = LessonTopic.objects.create(
                plan=curriculum_plan,
                lesson_number=lesson_number,
                topic=topic_text,
                homework=homework,
                lesson_type=lesson_type,
                group=group
            )
            created_lessons_count += 1
            logger.debug(f"Створено Lesson: {lesson_topic.id} для дати {lesson_item['date']}")

            # Також створюємо відповідний об'єкт Lesson у journal.models
            # з датою, яка була згенерована на фронтенді
            Lesson.objects.create(
                lesson_topic=lesson_topic,
                date=date.fromisoformat(lesson_item['date']),
                teacher=user_teacher,
                school_class=school_class,
                subject=subject
            )

        logger.info(
            f"Загальна кількість створених уроків: {created_lessons_count}")

        return JsonResponse(
            {'status': 'success', 'message': f'План та {created_lessons_count} тем уроків успішно збережено.'})
    except json.JSONDecodeError:
        logger.error("JSONDecodeError in save_plan_and_lessons", exc_info=True)
        return JsonResponse({'status': 'error', 'message': 'Недійсний JSON-запит.'}, status=400)
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"Помилка при збереженні плану та уроків: {e}", exc_info=True)  # Логуємо помилку
        return JsonResponse({'status': 'error', 'message': f"Помилка при збереженні плану: {e}"}, status=500)
