from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import User, Profile
from .forms import UserUpdateForm, ProfileUpdateForm


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


@login_required # Цей декоратор вже перевіряє, чи користувач автентифікований
# @role_required(['admin', 'teacher', 'curator', 'student', 'parent']) # Якщо всі ролі мають доступ
def profile_view(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        # Логіка дозволів на редагування всередині представлення
        if user.is_admin():
            pass # Адмін може редагувати все
        elif user.is_teacher() or user.is_curator():
            if 'year_of_birth' in profile_form.fields:
                del profile_form.fields['year_of_birth']
            if 'admission_year' in profile_form.fields:
                del profile_form.fields['admission_year']
        elif user.is_student() or user.is_parent():
            messages.error(request, 'У вас немає дозволу на редагування профілю.')
            return redirect('profile')

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Ваш профіль успішно оновлено!')
            return redirect('profile')
        else:
            messages.error(request, 'Будь ласка, виправте помилки у формі.')

    else: # GET запит
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=profile)

    # Логіка для відображення форм (та блокування полів) залежно від ролі
    can_edit = True
    if user.is_admin():
        pass
    elif user.is_teacher() or user.is_curator():
        profile_form.fields['year_of_birth'].widget.attrs['readonly'] = True
        profile_form.fields['year_of_birth'].help_text = 'Рік народження не можна редагувати.'
        profile_form.fields['admission_year'].widget.attrs['readonly'] = True
        profile_form.fields['admission_year'].help_text = 'Рік вступу не можна редагувати.'
    elif user.is_student() or user.is_parent():
        for field_name in user_form.fields:
            user_form.fields[field_name].widget.attrs['readonly'] = True
        for field_name in profile_form.fields:
            profile_form.fields[field_name].widget.attrs['readonly'] = True
        can_edit = False

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile_user': user,
        'profile': profile,
        'can_edit': can_edit,
    }
    return render(request, 'users/profile.html', context)