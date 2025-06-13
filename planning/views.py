# # planning/views.py
#
# from datetime import date, timedelta
# import json
# from collections import defaultdict
# import logging
#
# from django.http import JsonResponse
# from django.views.decorators.http import require_POST
# from django.views.decorators.csrf import csrf_protect
# from django.shortcuts import get_object_or_404
#
# from core.models import SchoolClass, Subject
# from planning.models import LessonTopic, CurriculumPlan  # Переконайтесь, що всі потрібні моделі імпортовані
#
# logger = logging.getLogger(__name__)
#
# @require_POST
# @csrf_protect
# def generate_lessons_for_plan(request, class_id, subject_id):
#     try:
#         school_class = get_object_or_404(SchoolClass, pk=class_id)
#         subject = get_object_or_404(Subject, pk=subject_id)
#         teacher = request.user.teacher # Припускаємо, що вчитель береться з request.user
#
#         academic_year_start_str = request.POST.get('academic_year_start')
#         academic_year_end_str = request.POST.get('academic_year_end')
#         selected_days_js_names = request.POST.getlist('lesson_frequency_days[]')
#         vacation_periods_json = request.POST.get('vacation_periods_json', '[]')
#
#         semester_1_start_str = request.POST.get('semester_1_start')
#         semester_1_end_str = request.POST.get('semester_1_end')
#         semester_2_start_str = request.POST.get('semester_2_start')
#         semester_2_end_str = request.POST.get('semester_2_end')
#
#         # 1. Парсинг дат
#         academic_year_start = date.fromisoformat(academic_year_start_str)
#         academic_year_end = date.fromisoformat(academic_year_end_str)
#
#         # Парсинг дат семестрів (можуть бути порожніми)
#         semester_1_start = date.fromisoformat(semester_1_start_str) if semester_1_start_str else None
#         semester_1_end = date.fromisoformat(semester_1_end_str) if semester_1_end_str else None
#         semester_2_start = date.fromisoformat(semester_2_start_str) if semester_2_start_str else None
#         semester_2_end = date.fromisoformat(semester_2_end_str) if semester_2_end_str else None
#
#         # Парсинг канікул у множину дат для швидкого пошуку
#         vacation_periods_raw = json.loads(vacation_periods_json)
#         vacation_dates_set = set()
#         for period in vacation_periods_raw:
#             start_vac = date.fromisoformat(period['start'])
#             end_vac = date.fromisoformat(period['end'])
#             current_date = start_vac
#             while current_date <= end_vac:
#                 vacation_dates_set.add(current_date)
#                 current_date += timedelta(days=1)
#
#         # Мапінг JS-назв днів тижня ('MON', 'TUE'...) до Python-чисел (0=Пн, ..., 6=Нд)
#         DAY_MAPPING = {
#             'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4, 'SAT': 5, 'SUN': 6
#         }
#         selected_weekdays_nums = [DAY_MAPPING[day] for day in selected_days_js_names if day in DAY_MAPPING]
#
#         generated_lessons = []
#         current_date = academic_year_start
#         lesson_number_counter = 1
#
#         # Отримуємо навчальні теми (LessonTopic) для даного плану
#         # Вам потрібно буде отримати CurriculumPlan, щоб фільтрувати теми за ним.
#         # Або ж, якщо теми не прив'язані до плану напряму, а до Subject/SchoolClass,
#         # то фільтруйте їх відповідно.
#         # Припустимо, що у вас є CurriculumPlan і до нього прив'язані CurriculumUnit, а до них LessonTopic.
#         try:
#             curriculum_plan = CurriculumPlan.objects.get(
#                 teacher=teacher,
#                 school_class=school_class,
#                 subject=subject,
#                 academic_year=school_class.academic_year_for_date(academic_year_start) # Або як ви визначаєте academic_year для плану
#             )
#             all_topics = LessonTopic.objects.filter(
#                 curriculum_unit__plan=curriculum_plan
#             ).order_by('curriculum_unit__order', 'lesson_number')
#             topic_iterator = iter(all_topics)
#         except CurriculumPlan.DoesNotExist:
#             return JsonResponse({'status': 'error', 'message': 'Календарний план не знайдено для генерації тем.'}, status=400)
#         except Exception as e:
#             logger.error(f"Error fetching lesson topics: {e}", exc_info=True)
#             topic_iterator = iter([]) # Порожній ітератор, щоб не було помилок далі
#
#         while current_date <= academic_year_end:
#             # 2. Перевірка дня тижня
#             if current_date.weekday() in selected_weekdays_nums:
#                 # 3. Перевірка на канікули
#                 if current_date not in vacation_dates_set:
#                     # 4. Перевірка на семестри
#                     is_in_active_semester = False
#                     if semester_1_start and semester_1_end and (semester_1_start <= current_date <= semester_1_end):
#                         is_in_active_semester = True
#                     if semester_2_start and semester_2_end and (semester_2_start <= current_date <= semester_2_end):
#                         is_in_active_semester = True
#
#                     # Якщо семестри не задані, вважаємо, що весь навчальний рік активний
#                     if not (semester_1_start or semester_2_start): # Жоден семестр не задано
#                         is_in_active_semester = True
#
#                     if is_in_active_semester:
#                         # Призначаємо тему уроку
#                         try:
#                             lesson_topic = next(topic_iterator)
#                         except StopIteration:
#                             # Якщо теми закінчилися, можна:
#                             # а) зупинити генерацію;
#                             # б) генерувати "пусті" уроки;
#                             # в) зациклити теми;
#                             # г) створити нові теми.
#                             lesson_topic = None # Або створіть заглушку для уроку
#
#                         generated_lessons.append({
#                             'lesson_number': lesson_number_counter,
#                             'date': current_date.isoformat(), # Важливо: ISO формат для JS
#                             'topic': lesson_topic.topic if lesson_topic else f'Тема {lesson_number_counter}',
#                             'lesson_type': lesson_topic.get_lesson_type_display() if lesson_topic and hasattr(lesson_topic, 'get_lesson_type_display') else '',
#                             'group': lesson_topic.get_group_display() if lesson_topic and hasattr(lesson_topic, 'get_group_display') else '',
#                             'homework': lesson_topic.homework if lesson_topic else '',
#                             'lesson_topic_id': lesson_topic.id if lesson_topic else None # Зберігаємо ID теми для подальшого збереження
#                         })
#                         lesson_number_counter += 1
#
#             current_date += timedelta(days=1)
#
#         return JsonResponse({'status': 'success', 'lessons': generated_lessons})
#
#     except Exception as e:
#         logger.exception("Помилка при генерації уроків для плану") # Детальний лог помилки
#         return JsonResponse({'status': 'error', 'message': f'Помилка генерації уроків: {str(e)}'}, status=400)