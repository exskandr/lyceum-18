from django.http import HttpResponseForbidden


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
