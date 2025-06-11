// frontend/static/frontend/js/journal.js
$(document).ready(function() {

    let allGradesByStudentLesson = {};
    let allAttendanceByStudentLesson = {};
    let lessonTopicsData = {};
    let gradeTypeMap = new Map();
    let groupMap = new Map();

    // Функція для оновлення вмісту display-mode в клітинці
    function updateDisplayMode($cell, gradeData, attendanceData, lessonGroup) {
        let parts = [];

        if (attendanceData && !attendanceData.is_present) {
            let attPart = '<span class="attendance-status">Н</span>';
            if (attendanceData.reason) {
                let reasonDisplay = attendanceData.reason.length > 10 ? attendanceData.reason.substring(0, 10) + '...' : attendanceData.reason;
                attPart += ' <span class="attendance-reason">(' + reasonDisplay + ')</span>';
            }
            parts.push(attPart);
        } else if (gradeData && Object.keys(gradeData).length > 0) {
            let gradeValue = gradeData.value;
            let gradeTypeDisplay = gradeData.grade_type_display;

            let gradePart = '<span class="grade-value">' + gradeValue + '</span>';
            if (gradeTypeDisplay) {
                gradePart += ' <span class="grade-type-display">(' + gradeTypeDisplay + ')</span>';
            }
            parts.push(gradePart);
        } else {
            parts.push('<span class="placeholder">-</span>');
        }

        $cell.find('.display-mode').html(parts.join('<br>'));
    }


    // Отримуємо дані з Django, які були передані через json_script
    try {
        const gradesDataElement = document.getElementById('grades_data');
        if (gradesDataElement) {
            allGradesByStudentLesson = JSON.parse(gradesDataElement.textContent);
        } else {
            console.error("DEBUG: Element with ID 'grades_data' not found!");
        }

        const attendanceDataElement = document.getElementById('attendance_data');
        if (attendanceDataElement) {
            allAttendanceByStudentLesson = JSON.parse(attendanceDataElement.textContent);
        } else {
            console.error("DEBUG: Element with ID 'attendance_data' not found!");
        }

        const lessonTopicsDataElement = document.getElementById('lesson_topics_data');
        if (lessonTopicsDataElement) {
            lessonTopicsData = JSON.parse(lessonTopicsDataElement.textContent);
        } else {
            console.error("DEBUG: Element with ID 'lesson_topics_data' not found!");
        }

        const gradeTypesChoicesDataElement = document.getElementById('grade_types_choices_data');
        if (gradeTypesChoicesDataElement) {
            JSON.parse(gradeTypesChoicesDataElement.textContent).forEach(item => gradeTypeMap.set(item[0], item[1]));
        } else {
            console.error("DEBUG: Element with ID 'grade_types_choices_data' not found!");
        }

        const groupChoicesDataElement = document.getElementById('group_choices_data');
        if (groupChoicesDataElement) {
            JSON.parse(groupChoicesDataElement.textContent).forEach(item => groupMap.set(String(item[0]), item[1]));
        } else {
            console.error("DEBUG: Element with ID 'group_choices_data' not found!");
        }

    } catch (e) {
        console.error("Помилка парсингу JSON даних з Django (DEBUG):", e);
    }

    // Ініціалізація display-mode при завантаженні сторінки
    $('.journal-cell').each(function() {
        let $cell = $(this);
        let studentId = $cell.data('student-id');
        let lessonId = $cell.data('lesson-id');

        let gradeForThisCell = allGradesByStudentLesson[studentId] ? allGradesByStudentLesson[studentId][lessonId] : null;
        let attendanceForThisCell = allAttendanceByStudentLesson[studentId] ? allAttendanceByStudentLesson[studentId][lessonId] : null;
        let lessonGroup = lessonTopicsData[lessonId] ? lessonTopicsData[lessonId].group : null;

        updateDisplayMode($cell, gradeForThisCell, attendanceForThisCell, lessonGroup);
    });

    // Обробка кліку на клітинку для перемикання в режим редагування
    $('.journal-cell').on('click', function(e) {
        if (!$(this).find('.edit-mode').hasClass('hidden') && $(e.target).closest('.edit-mode').length && $(e.target).is('select, input, button')) {
            return;
        }

        e.stopPropagation();

        let $currentCell = $(this);

        $('.journal-cell .edit-mode').not($currentCell.find('.edit-mode')).addClass('hidden');
        $('.journal-cell .display-mode').not($currentCell.find('.display-mode')).removeClass('hidden');

        $currentCell.find('.display-mode').addClass('hidden');
        $currentCell.find('.edit-mode').removeClass('hidden');

        $currentCell.find('.edit-mode :input:visible').first().focus();
    });

    // Приховати режим редагування при кліку поза поточною клітинкою
    $(document).on('click', function(e) {
        if (!$(e.target).closest('.journal-cell').length) {
            $('.journal-cell .edit-mode').addClass('hidden');
            $('.journal-cell .display-mode').removeClass('hidden');
        }
    });

    // Обробка зміни чекбоксу відвідуваності
    $('.attendance-checkbox').change(function() {
        let $form = $(this).closest('.attendance-form');
        if ($(this).is(':checked')) {
            $form.find('input[name="reason"]').hide().val('');
        } else {
            $form.find('input[name="reason"]').show();
        }
    }).trigger('change');


    // Обробка відправки форми оцінки (AJAX)
    $('.grade-form').submit(function(e) {
        e.preventDefault();
        let $form = $(this);
        let $cell = $form.closest('.journal-cell');
        let studentId = $form.data('student-id');
        let lessonId = $form.data('lesson-id');
        let gradeId = $form.find('input[name="grade_id"]').val();
        let gradeValue = $form.find('input[name="grade_value"]').val();
        let gradeType = $form.find('select[name="grade_type"]').val();
        //let gradeTypeDisplay = $form.find('select[name="grade_type"] option:selected').text();
        let csrfToken = $form.find('input[name="csrfmiddlewaretoken"]').val();

        // Валідація
        if (!gradeValue && gradeId) {
            if (!confirm("Ви впевнені, що хочете видалити цю оцінку?")) {
                return;
            }
        } else if (gradeValue && (gradeValue < 1 || gradeValue > 12)) {
            alert("Оцінка має бути від 1 до 12.");
            return;
        } else if (!gradeValue && !gradeId) { // Забороняємо створювати порожню оцінку
             alert("Будь ласка, введіть оцінку.");
             return;
        }

        let requestData = {
            'student_id': studentId,
            'lesson_id': lessonId,
            'grade_value': gradeValue,
            'grade_type': gradeType,
            'csrfmiddlewaretoken': csrfToken
        };

        if (gradeId) {
            requestData['grade_id'] = gradeId;
        }

        $.ajax({
            url: '/teacher/update-grade/',
            type: 'POST',
            data: requestData,
            success: function(response) {
                if (response.status === 'success') {
                    allGradesByStudentLesson[studentId] = allGradesByStudentLesson[studentId] || {};

                    if (response.grade_id) { // Оцінка збережена/оновлена
                        $form.find('input[name="grade_id"]').val(response.grade_id);
                        $form.find('input[name="grade_value"]').val(response.grade_value);
                        $form.find('select[name="grade_type"]').val(response.grade_type);

                        allGradesByStudentLesson[studentId][lessonId] = {
                            'value': response.grade_value,
                            'id': response.grade_id,
                            'comment': '',
                            'grade_type': response.grade_type,
                            'grade_type_display': response.grade_type_display || gradeTypeMap.get(response.grade_type)
                        };
                    } else { // Оцінка видалена
                        $form.find('input[name="grade_id"]').val('');
                        $form.find('input[name="grade_value"]').val('');
                        $form.find('select[name="grade_type"]').val('current'); // Скинути до дефолту

                        delete allGradesByStudentLesson[studentId][lessonId];
                    }

                    // Оновлюємо відображення клітинки
                    let gradeForThisCell = allGradesByStudentLesson[studentId] ? allGradesByStudentLesson[studentId][lessonId] : null;
                    let attendanceForThisCell = allAttendanceByStudentLesson[studentId] ? allAttendanceByStudentLesson[studentId][lessonId] : null;
                    let lessonGroup = lessonTopicsData[lessonId] ? lessonTopicsData[lessonId].group : null;
                    updateDisplayMode($cell, gradeForThisCell, attendanceForThisCell, lessonGroup);

                    // Приховуємо форму після успішного збереження/видалення
                    $cell.find('.edit-mode').addClass('hidden');
                    $cell.find('.display-mode').removeClass('hidden');

                } else {
                    alert('Помилка: ' + response.message);
                }
            },
            error: function(xhr, status, error) {
                alert('Помилка при збереженні оцінки: ' + xhr.responseText);
                console.error("AJAX Error (update_grade):", xhr.responseText);
            }
        });
    });

    // Обробка відправки форми відвідуваності (AJAX)
    $('.attendance-form').submit(function(e) {
        e.preventDefault();
        let $form = $(this);
        let $cell = $form.closest('.journal-cell');
        let studentId = $form.data('student-id');
        let lessonId = $form.data('lesson-id');
        let attendanceId = $form.find('input[name="attendance_id"]').val();
        let isPresent = $form.find('input[name="is_present"]').is(':checked');
        let reason = $form.find('input[name="reason"]').val();
        let csrfToken = $form.find('input[name="csrfmiddlewaretoken"]').val();

        let requestData = {
            'student_id': studentId,
            'lesson_id': lessonId,
            'is_present': isPresent,
            'reason': reason,
            'csrfmiddlewaretoken': csrfToken
        };

        if (attendanceId) {
            requestData['attendance_id'] = attendanceId;
        }

        $.ajax({
            url: '/teacher/update-attendance/',
            type: 'POST',
            data: requestData,
            success: function(response) {
                if (response.status === 'success') {
                    allAttendanceByStudentLesson[studentId] = allAttendanceByStudentLesson[studentId] || {};

                    if (response.attendance_id) { // Відвідуваність збережена/оновлена
                        $form.find('input[name="attendance_id"]').val(response.attendance_id);
                        $form.find('input[name="is_present"]').prop('checked', response.is_present);
                        $form.find('input[name="reason"]').val(response.reason);

                        allAttendanceByStudentLesson[studentId][lessonId] = {
                            'id': response.attendance_id,
                            'is_present': response.is_present,
                            'reason': response.reason
                        };
                    } else { // Відвідуваність видалена (якщо is_present=true і немає причини)
                        $form.find('input[name="attendance_id"]').val('');
                        $form.find('input[name="is_present"]').prop('checked', true); // За замовчуванням присутній
                        $form.find('input[name="reason"]').val('').hide();

                        delete allAttendanceByStudentLesson[studentId][lessonId];
                    }

                    // Оновлюємо відображення клітинки
                    let gradeForThisCell = allGradesByStudentLesson[studentId] ? allGradesByStudentLesson[studentId][lessonId] : null;
                    let attendanceForThisCell = allAttendanceByStudentLesson[studentId] ? allAttendanceByStudentLesson[studentId][lessonId] : null;
                    let lessonGroup = lessonTopicsData[lessonId] ? lessonTopicsData[lessonId].group : null;
                    updateDisplayMode($cell, gradeForThisCell, attendanceForThisCell, lessonGroup);

                    // Приховуємо форму після успішного збереження/видалення
                    $cell.find('.edit-mode').addClass('hidden');
                    $cell.find('.display-mode').removeClass('hidden');

                } else {
                    alert('Помилка: ' + response.message);
                }
            },
            error: function(xhr, status, error) {
                alert('Помилка при збереженні відвідуваності: ' + xhr.responseText);
                console.error("AJAX Error (update_attendance):", xhr.responseText);
            }
        });
    });
});