// frontend/static/frontend/js/planning_select_class_subject.js
$(document).ready(function() {

    $('#goToPlanningBtn').on('click', function() {
        const classId = $('#selectClass').val();
        const subjectId = $('#selectSubject').val();

        if (classId && subjectId) {
            // Отримуємо базовий URL з data-атрибута кнопки
            let baseUrl = $(this).data('planning-url');
            // Замінюємо заглушки (0) на реальні значення
            let finalUrl = baseUrl.replace('/0/0/', `/${classId}/${subjectId}/`);
            // Або, якщо URL завжди має вигляд /path/to/class_id/subject_id/
            // let finalUrl = baseUrl.replace('0/', classId + '/').replace('0/', subjectId + '/'); // Для послідовної заміни

            window.location.href = finalUrl;
        } else {
            alert('Будь ласка, виберіть клас та предмет.');
        }
    });

    $('#goToJournalBtn').on('click', function() {
        const classId = $('#selectClass').val();
        const subjectId = $('#selectSubject').val();

        if (classId && subjectId) {
            let baseUrl = $(this).data('journal-url');
            let finalUrl = baseUrl.replace('/0/0/', `/${classId}/${subjectId}/`);

            window.location.href = finalUrl;
        } else {
            alert('Будь ласка, виберіть клас та предмет.');
        }
    });
});