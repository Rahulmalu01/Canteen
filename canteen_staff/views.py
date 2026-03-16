"""canteen_staff/views.py — Staff login + menu management + daily orders"""

from datetime import date

from django.contrib import messages
from django.contrib.auth import login
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.forms import RoleLoginForm, MenuItemForm
from accounts.models import User, Category, MenuItem, Order


def _staff_only(view_fn):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != User.ROLE_CANTEEN:
            messages.error(request, "Please log in as Canteen Staff.")
            return redirect('staff_login')
        return view_fn(request, *args, **kwargs)
    wrapper.__name__ = view_fn.__name__
    return wrapper


# ── Auth ─────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated and request.user.role == User.ROLE_CANTEEN:
        return redirect('staff_dashboard')

    form = RoleLoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if user.role != User.ROLE_CANTEEN:
            messages.error(request, "⛔ This portal is for Canteen Staff only.")
        else:
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name or user.username}!")
            return redirect('staff_dashboard')
    return render(request, 'canteen_staff/login.html', {'form': form})


# ── Dashboard ────────────────────────────────────────────────────────────────

@_staff_only
def dashboard(request):
    today = date.today()
    return render(request, 'canteen_staff/dashboard.html', {
        'daily_orders':      Order.objects.filter(created_at__date=today).count(),
        'daily_revenue':     Order.objects.filter(created_at__date=today)
                                  .aggregate(t=Sum('total_amount'))['t'] or 0,
        'menu_count':        MenuItem.objects.count(),
        'unavailable_count': MenuItem.objects.filter(is_available=False).count(),
    })


# ── Menu Management ──────────────────────────────────────────────────────────

@_staff_only
def menu_management(request):
    return render(request, 'canteen_staff/menu_management.html', {
        'items':      MenuItem.objects.select_related('category').order_by('category__name', 'name'),
        'categories': Category.objects.all(),
    })


@_staff_only
def add_menu_item(request):
    form = MenuItemForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Menu item added successfully.")
        return redirect('menu_management')
    return render(request, 'canteen_staff/add_edit_item.html', {'form': form, 'action': 'Add'})


@_staff_only
def edit_menu_item(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    form = MenuItemForm(request.POST or None, request.FILES or None, instance=item)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"'{item.name}' updated.")
        return redirect('menu_management')
    return render(request, 'canteen_staff/add_edit_item.html',
                  {'form': form, 'action': 'Edit', 'item': item})


@require_POST
@_staff_only
def delete_menu_item(request, item_id):
    get_object_or_404(MenuItem, id=item_id).delete()
    messages.success(request, "Item deleted.")
    return redirect('menu_management')


@require_POST
@_staff_only
def toggle_availability(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    item.is_available = not item.is_available
    item.save(update_fields=['is_available'])
    return JsonResponse({'success': True, 'is_available': item.is_available})


@_staff_only
def daily_orders(request):
    today = date.today()
    orders = (Order.objects.filter(created_at__date=today)
              .prefetch_related('items__menu_item')
              .select_related('student'))
    return render(request, 'canteen_staff/daily_orders.html',
                  {'orders': orders, 'today': today})
