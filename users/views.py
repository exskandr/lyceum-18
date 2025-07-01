from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import User, Profile
from .forms import UserUpdateForm, ProfileUpdateForm

import datetime


def role_required(allowed_roles):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Unauthorized")
            if request.user.role not in allowed_roles:
                return HttpResponseForbidden("Access denied")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# @login_required # Цей декоратор вже перевіряє, чи користувач автентифікований
# # @role_required(['admin', 'teacher', 'curator', 'student', 'parent']) # Якщо всі ролі мають доступ
# def profile_view(request):
#     user = request.user
#     profile = user.profile
#
#     if request.method == 'POST':
#         user_form = UserUpdateForm(request.POST, instance=user)
#         profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
#
#         # Логіка дозволів на редагування всередині представлення
#         if user.is_admin():
#             pass # Адмін може редагувати все
#         elif user.is_teacher() or user.is_curator():
#             if 'year_of_birth' in profile_form.fields:
#                 del profile_form.fields['year_of_birth']
#             if 'admission_year' in profile_form.fields:
#                 del profile_form.fields['admission_year']
#         elif user.is_student() or user.is_parent():
#             messages.error(request, 'У вас немає дозволу на редагування профілю.')
#             return redirect('profile')
#
#         if user_form.is_valid() and profile_form.is_valid():
#             user_form.save()
#             profile_form.save()
#             messages.success(request, 'Ваш профіль успішно оновлено!')
#             return redirect('profile')
#         else:
#             messages.error(request, 'Будь ласка, виправте помилки у формі.')
#
#     else: # GET запит
#         user_form = UserUpdateForm(instance=user)
#         profile_form = ProfileUpdateForm(instance=profile)
#
#     # Логіка для відображення форм (та блокування полів) залежно від ролі
#     can_edit = True
#     if user.is_admin():
#         pass
#     elif user.is_teacher() or user.is_curator():
#         profile_form.fields['year_of_birth'].widget.attrs['readonly'] = True
#         profile_form.fields['year_of_birth'].help_text = 'Рік народження не можна редагувати.'
#         profile_form.fields['admission_year'].widget.attrs['readonly'] = True
#         profile_form.fields['admission_year'].help_text = 'Рік вступу не можна редагувати.'
#     elif user.is_student() or user.is_parent():
#         for field_name in user_form.fields:
#             user_form.fields[field_name].widget.attrs['readonly'] = True
#         for field_name in profile_form.fields:
#             profile_form.fields[field_name].widget.attrs['readonly'] = True
#         can_edit = False
#
#     context = {
#         'user_form': user_form,
#         'profile_form': profile_form,
#         'profile_user': user,
#         'profile': profile,
#         'can_edit': can_edit,
#     }
#     return render(request, 'users/profile.html', context)

@login_required
def profile_view(request):
    user = request.user
    if not hasattr(user, 'profile') or user.profile is None:
        Profile.objects.create(user=user)
    profile = user.profile

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        # --- Логіка дозволів на збереження (для POST запитів) ---
        if user.is_admin():
            pass
        elif user.is_teacher() or user.is_curator():
            # remove these fields from the form so that they are not processed even if someone tries to submit them
            if 'year_of_birth' in profile_form.fields:
                del profile_form.fields['year_of_birth']
            if 'admission_year' in profile_form.fields:
                del profile_form.fields['admission_year']
        elif user.is_student() or user.is_parent():
            messages.error(request, 'У вас немає дозволу на редагування профілю.')
            # Учні та батьки не мають дозволу на редагування.
            return redirect('profile')

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Ваш профіль успішно оновлено!')
            return redirect('profile')
        else:
            messages.error(request, 'Будь ласка, виправте помилки у формі.')

    else:  # GET запит (коли сторінка просто завантажується)
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=profile)

        # --- ЛОГІКА ДЛЯ ПРИХОВУВАННЯ ПОЛІВ НА ОСНОВІ РОЛІ ---
        can_edit = True  # За замовчуванням дозволено редагування

        if user.is_admin():
            pass # Адмін бачить і може редагувати всі поля
        elif user.is_teacher() or user.is_curator():
            # Для вчителів/класних керівників, приховуємо поля року народження та року вступу
            # Шляхом їх видалення з об'єкта форми для відображення
            if 'year_of_birth' in profile_form.fields:
                del profile_form.fields['year_of_birth']
            if 'admission_year' in profile_form.fields:
                del profile_form.fields['admission_year']
            if profile.start_work_year:
                current_year = datetime.datetime.now().year
                work_experience_years = current_year - profile.start_work_year
                # Можна додати більш детальну логіку, наприклад, "5 років" або "менше року"
                if work_experience_years > 0:
                    if work_experience_years < 2:
                        work_experience = f"{work_experience_years} рік"
                    if work_experience_years > 2 or work_experience_years < 5:
                        work_experience = f"{work_experience_years} роки"
                    if work_experience_years >= 5:
                        work_experience = f"{work_experience_years} років"
                elif work_experience_years == 0:
                    work_experience = "менше року"
                else:  # Якщо рік початку роботи в майбутньому або помилковий
                    work_experience = "Невідомо"
            else:
                work_experience = "Не вказано"
            # Інші поля залишаються видимими та редагованими
        elif user.is_student() or user.is_parent():
            user_form.fields = {}
            profile_form.fields = {}
            can_edit = False

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile_user': user,
        'profile': profile,
        'can_edit': can_edit,
        'work_experience': work_experience,
    }
    return render(request, 'users/profile.html', context)