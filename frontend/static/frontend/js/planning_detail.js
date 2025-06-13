// frontend/static/frontend/js/planning_detail.js
$(document).ready(function() {
    const $detailedLessonsTableBody = $('#detailed-lessons-table tbody');
    const $saveAllDetailedLessonsBtn = $('#save-all-detailed-lessons-btn');

    const lessonTypeChoices = JSON.parse(document.getElementById('lesson_type_choices_data').textContent);
    const groupChoices = JSON.parse(document.getElementById('group_choices_data').textContent);
    // lesson_dates_by_topic_number will contain actual lesson dates from `journal.models.Lesson`
    const lessonDatesByTopicNumber = JSON.parse(document.getElementById('lesson_dates_by_topic_number').textContent);

    // Функція для заповнення дат уроків на сторінці деталей
    function populateLessonDates() {
        $detailedLessonsTableBody.find('tr').each(function() {
            const $row = $(this);
            const lessonNumber = $row.find('.lesson-date-cell').data('lesson-number');
            const lessonDate = lessonDatesByTopicNumber[lessonNumber];
            if (lessonDate) {
                $row.find('.lesson-date-cell').text(moment(lessonDate).format('DD.MM.YYYY (ddd)'));
            } else {
                $row.find('.lesson-date-cell').text('Дата не визначена');
            }
        });
    }

    populateLessonDates(); // Викликаємо при завантаженні сторінки

    // Обробник для кнопки "Зберегти" для окремого рядка
    $detailedLessonsTableBody.on('click', '.save-lesson-topic-row', function() {
        const $row = $(this).closest('tr');
        const lessonTopicId = $row.find('.lesson-topic-id').val();
        const topicText = $row.find('.lesson-topic-text').val().trim();
        const lessonType = $row.find('.lesson-type-select').val();
        const group = $row.find('.lesson-group-select').val();
        const homework = $row.find('.lesson-homework').val().trim();

        if (!topicText) {
            alert('Тема уроку не може бути порожньою.');
            return;
        }

        const dataToSave = {
            lesson_topic_id: lessonTopicId,
            topic: topicText,
            lesson_type: lessonType,
            group: group === '' ? null : parseInt(group), // Конвертуємо порожній рядок в null
            homework: homework,
        };

        $.ajax({
            url: `{% url 'save_plan_and_lessons' class_id=school_class.id subject_id=subject.id %}`, // Використовуємо той самий ендпоінт, що й для збереження всього плану
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                single_lesson_update: true, // Додаємо прапорець, щоб бекенд знав, що це оновлення одного уроку
                lesson_data: dataToSave,
                // Передаємо також дані про CurriculumPlan, щоб оновити його, якщо це не перше збереження
                academic_year: $('#academic_year').val(), // Цих полів немає на детальному шаблоні, їх потрібно отримати з CurriculumPlan в view
                academic_year_start: '{{ curriculum_plan.academic_year_start|date:"Y-m-d" }}',
                academic_year_end: '{{ curriculum_plan.academic_year_end|date:"Y-m-d" }}',
                semester_1_start: '{{ curriculum_plan.semester_1_start|date:"Y-m-d"|default:"" }}',
                semester_1_end: '{{ curriculum_plan.semester_1_end|date:"Y-m-d"|default:"" }}',
                semester_2_start: '{{ curriculum_plan.semester_2_start|date:"Y-m-d"|default:"" }}',
                semester_2_end: '{{ curriculum_plan.semester_2_end|date:"Y-m-d"|default:"" }}',
                lesson_frequency_days: [], // Ці дані можуть бути недоступні, якщо не передані
                vacation_periods_json: '{{ curriculum_plan.vacation_periods_json|escapejs|safe }}'
            }),
            headers: {
                'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.status === 'success') {
                    alert('Урок успішно оновлено!');
                    // Можливо, оновити лише цей рядок, якщо бекенд повертає оновлені дані
                } else {
                    alert('Помилка оновлення уроку: ' + response.message);
                }
            },
            error: function(xhr, status, error) {
                alert('Помилка AJAX-запиту: ' + error);
                console.error(xhr.responseText);
            }
        });
    });

    // Можна додати обробник для кнопки "Зберегти всі зміни" (якщо є така кнопка)
    // Він буде збирати всі дані з таблиці та відправляти їх на бекенд аналогічно save_plan_and_lessons
    // Але зараз у нас є кнопка для кожного рядка, що простіше для користувача.
});