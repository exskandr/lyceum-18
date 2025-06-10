from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy


class RoleRequiredMixin(AccessMixin):
    """
    Mixin to check if the user has a specific role.
    Usage: @method_decorator(role_required('teacher'))
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        required_roles = getattr(self, 'required_roles', [])

        # if not any(getattr(request.user, f'is_{role}_role')() for role in required_roles):
        if not any(getattr(request.user, f'is_{role}')() for role in required_roles):
            # Перевірка на суперюзера, який завжди має повний доступ
            if not request.user.is_superuser:
                return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


# Функціональні декоратори
def teacher_required(function=None):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            if request.user.is_authenticated and (
                    # request.user.is_teacher_role() or request.user.is_curator_role() or request.user.is_superuser):
                    request.user.is_teacher() or request.user.is_curator() or request.user.is_superuser):
                return view_func(request, *args, **kwargs)
            else:
                return redirect(reverse_lazy('login'))  # Або інша сторінка з повідомленням про відсутність дозволів

        return wrapper_func

    return decorator(function) if function else decorator


def student_required(function=None):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            if request.user.is_authenticated and (request.user.is_student() or request.user.is_superuser):
                return view_func(request, *args, **kwargs)
            else:
                return redirect(reverse_lazy('login'))

        return wrapper_func

    return decorator(function) if function else decorator


def parent_required(function=None):
    def decorator(view_func):
        def wrapper_func(request, *args, **kwargs):
            if request.user.is_authenticated and (request.user.is_parente() or request.user.is_superuser):
                return view_func(request, *args, **kwargs)
            else:
                return redirect(reverse_lazy('login'))

        return wrapper_func

    return decorator(function) if function else decorator
