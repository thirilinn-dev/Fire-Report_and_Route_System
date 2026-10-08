from functools import wraps
from django.shortcuts import render, redirect
from django.urls import reverse

def role_required(*allowed_roles):
    """
    Decorator for views that checks if the user is logged in and has
    one of the specified roles or aliases.
    If unauthenticated, redirects to login URL with 'next' parameter.
    If unauthorized, renders 403 Forbidden CAD interface.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not getattr(request, 'user', None) or not request.user.is_authenticated:
                login_url = reverse('login')
                return redirect(f"{login_url}?next={request.path}")

            # Administrators always bypass role restrictions
            if getattr(request.user, 'is_admin', False):
                return view_func(request, *args, **kwargs)

            # Check if user has one of the allowed roles
            has_permission = False
            if hasattr(request.user, 'has_role'):
                has_permission = request.user.has_role(*allowed_roles)

            if not has_permission:
                context = {
                    'required_roles': list(allowed_roles),
                    'user_role': getattr(request.user, 'role_name', 'None'),
                    'attempted_url': request.path,
                }
                return render(request, '403.html', context, status=403)

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def admin_required(view_func):
    """Decorator restricting view to Administrators only."""
    return role_required('Admin', 'Administrator')(view_func)


def dispatcher_required(view_func):
    """Decorator restricting view to Dispatchers, Operators, Station Admins, and Administrators."""
    return role_required('Dispatcher', 'Operator', 'Station Admin', 'Admin', 'Administrator')(view_func)


def responder_required(view_func):
    """Decorator restricting view to Firefighters, Dispatchers, and Administrators."""
    return role_required(
        'Firefighter', 'Responder', 'Dispatcher', 'Operator', 'Admin', 'Administrator'
    )(view_func)
