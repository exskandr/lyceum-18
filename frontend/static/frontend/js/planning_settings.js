// frontend/static/frontend/js/planning_settings.js
$(document).ready(function() {
    console.log("Document is ready.");

    const djangoJsDataElement = document.getElementById('django_js_data');

    // Перевірка, чи елемент існує, перш ніж намагатися його парсити
    if (!djangoJsDataElement) {
        console.error("Помилка: Елемент з id='django_js_data' не знайдено в DOM. Перевірте planning_settings.html.");
        return; // Зупиняємо виконання, якщо дані не завантажені
    }

    const DJANGO_DATA = JSON.parse(djangoJsDataElement.textContent);
    console.log("DJANGO_DATA:", DJANGO_DATA); // Тепер цей лог покаже вміст DJANGO_DATA

    const classId = DJANGO_DATA.class_id;
    const subjectId = DJANGO_DATA.subject_id;
    const generateLessonsUrlTemplate = DJANGO_DATA.generate_lessons_url_template;
    const savePlanAndLessonsUrlTemplate = DJANGO_DATA.save_plan_and_lessons_url_template;
    const pythonDaysOfWeekMap = DJANGO_DATA.python_days_of_week_map;
    const lessonTypeChoices = DJANGO_DATA.lesson_type_choices; // Отримаємо тепер з DJANGO_DATA
    const groupChoices = DJANGO_DATA.group_choices;         // Отримаємо тепер з DJANGO_DATA
    const academicYearForPlan = DJANGO_DATA.academic_year_for_plan;

    // Встановлюємо локаль Moment.js на українську (якщо Moment.js завантажується з 'moment-with-locales.min.js')
    moment.locale('uk');
    const $planningSettingsForm = $('#planning-settings-form');
    const $generateLessonsBtn = $('#generate-lessons-btn');
    const $lessonsPreviewTableBody = $('#generated-lessons-preview-table tbody');
    const $saveAllLessonsBtn = $('#save-all-lessons-btn');

    let generatedLessonsData = [];


    // Функція для додавання рядка попереднього перегляду уроку
    function addLessonPreviewRow(lesson) {
        const rowHtml = `
            <tr>
                <td>${lesson.lesson_number}</td>
                <td>${moment(lesson.date).format('DD.MM.YYYY (ddd)')}</td>
                <td>${lesson.topic || '-'}</td>
                <td>${lesson.lesson_type || '-'}</td>
                <td>${lesson.group || '-'}</td>
                <td>${lesson.homework || '-'}</td>
            </tr>
        `;
        $lessonsPreviewTableBody.append(rowHtml);
    }

    // Обробник для кнопки "Згенерувати уроки"
    $generateLessonsBtn.on('click', function() {
        const academicYearStart = $('#academic_year_start').val();
        const academicYearEnd = $('#academic_year_end').val();
        const selectedDays = $('input[name="lesson_frequency_days[]"]:checked').map(function() {
            return $(this).val();
        }).get();

        const semester1Start = $('#semester_1_start').val();
        const semester1End = $('#semester_1_end').val();
        const semester2Start = $('#semester_2_start').val();
        const semester2End = $('#semester_2_end').val();

        const vacationPeriodsRaw = $('#vacation_periods').val().trim();
        let vacationPeriods = [];
        if (vacationPeriodsRaw) {
            const lines = vacationPeriodsRaw.split('\n');
            for (const line of lines) {
                const parts = line.split('-').map(p => p.trim());
                if (parts.length === 2 && moment(parts[0], 'YYYY-MM-DD').isValid() && moment(parts[1], 'YYYY-MM-DD').isValid()) {
                    vacationPeriods.push({
                        start: parts[0],
                        end: parts[1]
                    });
                } else {
                    alert('Будь ласка, перевірте формат канікул. Кожен період має бути "РРРР-ММ-ДД - РРРР-ММ-ДД"');
                    return;
                }
            }
        }

        if (!academicYearStart || !academicYearEnd || selectedDays.length === 0) {
            alert('Будь ласка, заповніть поля "Початок/Кінець навчального року" та оберіть дні проведення уроків.');
            return;
        }

        $lessonsPreviewTableBody.empty();
        $lessonsPreviewTableBody.html('<tr><td colspan="6" class="text-center">Генерація...</td></tr>');
        $saveAllLessonsBtn.hide();

        const generateLessonsUrl = generateLessonsUrlTemplate
                                    .replace('0/', classId + '/')
                                    .replace('0/', subjectId + '/');

        $.ajax({
//            url: `{% url 'generate_lessons_for_plan' class_id=school_class.id subject_id=subject.id %}`,
            url: generateLessonsUrl, // Використовуємо динамічно побудований URL
            type: 'POST',
            data: {
            csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val(),
                academic_year_start: academicYearStart,
                academic_year_end: academicYearEnd,
                semester_1_start: semester1Start, // Передаємо дати семестрів
                semester_1_end: semester1End,
                semester_2_start: semester2Start,
                semester_2_end: semester2End,
                'lesson_frequency_days[]': selectedDays,
                vacation_periods_json: JSON.stringify(vacationPeriods)
            },
            success: function(response) {
                $lessonsPreviewTableBody.empty();
                if (response.status === 'success') {
                    if (response.lessons.length > 0) {
                        generatedLessonsData = response.lessons;
                        response.lessons.forEach(addLessonPreviewRow);
                        $saveAllLessonsBtn.show();
                    } else {
                        $lessonsPreviewTableBody.html('<tr><td colspan="6" class="text-center">Немає уроків за заданими параметрами.</td></tr>');
                    }
                } else {
                    alert('Помилка генерації: ' + response.message);
                    $lessonsPreviewTableBody.html('<tr><td colspan="6" class="text-center">Помилка генерації.</td></tr>');
                }
            },
            error: function(xhr, status, error) {
                alert('Помилка AJAX-запиту: ' + error + '\nДеталі: ' + xhr.responseText); // Детальніше повідомлення про помилку
                console.error('AJAX Error:', xhr, status, error);
                $lessonsPreviewTableBody.html('<tr><td colspan="6" class="text-center">Помилка завантаження.</td></tr>');
            }
        });
    });

    // Обробник для кнопки "Зберегти план та уроки"
    $saveAllLessonsBtn.on('click', function() {
        if (!generatedLessonsData || generatedLessonsData.length === 0) {
            alert('Спочатку згенеруйте уроки.');
            console.warn("generatedLessonsData порожній при спробі збереження."); // <--- ДОДАЙТЕ ЦЕЙ ЛОГ
            return;
        }


        const academicYear = $('#academic_year').val();
        const academicYearStart = $('#academic_year_start').val();
        const academicYearEnd = $('#academic_year_end').val();
        const semester1Start = $('#semester_1_start').val();
        const semester1End = $('#semester_1_end').val();
        const semester2Start = $('#semester_2_start').val();
        const semester2End = $('#semester_2_end').val();
        const selectedDays = $('input[name="lesson_frequency_days[]"]:checked').map(function() {
            return $(this).val();
        }).get();

        const vacationPeriodsRaw = $('#vacation_periods').val().trim();
        let vacationPeriods = [];
        if (vacationPeriodsRaw) {
            const lines = vacationPeriodsRaw.split('\n');
            for (const line of lines) {
                const parts = line.split('-').map(p => p.trim());
                if (parts.length === 2 && moment(parts[0], 'YYYY-MM-DD').isValid() && moment(parts[1], 'YYYY-MM-DD').isValid()) {
                    vacationPeriods.push({
                        start: parts[0],
                        end: parts[1]
                    });
                }
            }
        }

        const saveLessonsUrl = savePlanAndLessonsUrlTemplate
                                .replace('0/', classId + '/')
                                .replace('0/', subjectId + '/');

        console.log("Відправлення на збереження. Кількість згенерованих уроків:", generatedLessonsData.length); // <--- ДОДАЙТЕ ЦЕЙ ЛОГ
        console.log("Перший згенерований урок (для перевірки):", generatedLessonsData[0]); // <--- ДОДАЙТЕ ЦЕЙ ЛОГ

        const planData = {
//            academic_year: academicYear,
            academic_year: academicYearForPlan,
            academic_year_start: academicYearStart,
            academic_year_end: academicYearEnd,
            semester_1_start: semester1Start,
            semester_1_end: semester1End,
            semester_2_start: semester2Start,
            semester_2_end: semester2End,
            lesson_frequency_days: selectedDays,
            vacation_periods_json: JSON.stringify(vacationPeriods),
            lessons: generatedLessonsData // Всі згенеровані уроки
        };

        $.ajax({
            url: saveLessonsUrl,
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(planData),
            headers: {
                'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
            },
            success: function(response) {
                if (response.status === 'success') {
                    alert(response.message);
                    window.location.href = `/teacher/planning/${classId}/${subjectId}/detail/`;
                } else {
                    alert('Помилка збереження: ' + response.message);
                }
            },
            error: function(xhr, status, error) {
                alert('Помилка AJAX-запиту: ' + error + '\nДеталі: ' + xhr.responseText);
                console.error('AJAX Error:', xhr, status, error);
            }
        });
    });
});
