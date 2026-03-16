"""admin_panel/views.py — Admin login + analytics + user/order management"""

import json
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.forms import RoleLoginForm
from accounts.models import User, Order, OrderItem


def _admin_only(view_fn):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != User.ROLE_ADMIN:
            messages.error(request, "Please log in as Admin.")
            return redirect('admin_login')
        return view_fn(request, *args, **kwargs)
    wrapper.__name__ = view_fn.__name__
    return wrapper


# ── Auth ─────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated and request.user.role == User.ROLE_ADMIN:
        return redirect('admin_dashboard')

    form = RoleLoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if user.role != User.ROLE_ADMIN:
            messages.error(request, "⛔ This portal is for Admins only.")
        else:
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name or user.username}! Admin dashboard loaded.")
            return redirect('admin_dashboard')
    return render(request, 'admin_panel/login.html', {'form': form})


# ── Dashboard (Analytics) ────────────────────────────────────────────────────

@_admin_only
def dashboard(request):
    today = date.today()

    # KPI cards
    total_users      = User.objects.exclude(role=User.ROLE_ADMIN).count()
    orders_today     = Order.objects.filter(created_at__date=today).count()
    revenue_today    = Order.objects.filter(created_at__date=today).aggregate(t=Sum('total_amount'))['t'] or 0
    pending_count    = Order.objects.filter(status=Order.STATUS_PENDING).count()

    # Revenue — last 7 days (Chart.js bar)
    labels, rev_data = [], []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        rev = Order.objects.filter(created_at__date=day).aggregate(t=Sum('total_amount'))['t'] or 0
        labels.append(day.strftime('%d %b'))
        rev_data.append(float(rev))

    # Top 5 items (Chart.js doughnut)
    top_items  = (OrderItem.objects
                  .values('menu_item__name')
                  .annotate(qty=Sum('quantity'))
                  .order_by('-qty')[:5])
    top_labels = [i['menu_item__name'] for i in top_items]
    top_data   = [i['qty'] for i in top_items]

    # Orders by status (status breakdown)
    status_counts = {s: Order.objects.filter(status=s).count()
                     for s, _ in Order.STATUS_CHOICES}

    return render(request, 'admin_panel/dashboard.html', {
        'total_users':    total_users,
        'orders_today':   orders_today,
        'revenue_today':  revenue_today,
        'pending_count':  pending_count,
        'revenue_labels': json.dumps(labels),
        'revenue_data':   json.dumps(rev_data),
        'top_labels':     json.dumps(top_labels),
        'top_data':       json.dumps(top_data),
        'status_counts':  status_counts,
    })


# ── User Management ──────────────────────────────────────────────────────────

@_admin_only
def user_management(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin_panel/users.html', {
        'users':        users,
        'role_choices': User.ROLE_CHOICES,
    })


@require_POST
@_admin_only
def change_role(request, user_id):
    user     = get_object_or_404(User, id=user_id)
    new_role = request.POST.get('role')
    if new_role in dict(User.ROLE_CHOICES):
        user.role = new_role
        user.save(update_fields=['role'])
        messages.success(request, f"{user.username}'s role → {user.get_role_display()}")
    return redirect('admin_user_management')


# ── All Orders ────────────────────────────────────────────────────────────────

@_admin_only
def all_orders(request):
    orders = (Order.objects.all()
              .select_related('student')
              .prefetch_related('items__menu_item'))
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    return render(request, 'admin_panel/orders.html', {
        'orders':         orders,
        'status_filter':  status_filter,
        'status_choices': Order.STATUS_CHOICES,
    })
