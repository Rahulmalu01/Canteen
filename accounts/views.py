"""
accounts/views.py — Landing page, student registration, logout
"""

from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect, render
from .forms import StudentRegistrationForm
from .models import User


def landing_view(request):
    """Root URL: authenticated users go to their dashboard, others see role-selector."""
    if request.user.is_authenticated:
        return redirect(request.user.get_dashboard_url())
    return render(request, 'landing.html')


def register_view(request):
    """Student self-registration only."""
    if request.user.is_authenticated:
        return redirect(request.user.get_dashboard_url())
    form = StudentRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        from django.contrib.auth import login
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome, {user.first_name}! Your account is ready.")
        return redirect('student_dashboard')
    return render(request, 'register.html', {'form': form})


def logout_view(request):
    role = getattr(request.user, 'role', None)
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('landing')
