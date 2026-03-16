"""kitchen/views.py — Kitchen staff login + order queue management"""

from django.contrib import messages
from django.contrib.auth import login
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.forms import RoleLoginForm
from accounts.models import User, Order


def _kitchen_only(view_fn):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != User.ROLE_KITCHEN:
            messages.error(request, "Please log in as Kitchen Staff.")
            return redirect('kitchen_login')
        return view_fn(request, *args, **kwargs)
    wrapper.__name__ = view_fn.__name__
    return wrapper


# ── Auth ─────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated and request.user.role == User.ROLE_KITCHEN:
        return redirect('kitchen_dashboard')

    form = RoleLoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if user.role != User.ROLE_KITCHEN:
            messages.error(request, "⛔ This portal is for Kitchen Staff only.")
        else:
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name or user.username}! Kitchen queue loaded.")
            return redirect('kitchen_dashboard')
    return render(request, 'kitchen/login.html', {'form': form})


# ── Dashboard (Kanban Queue) ─────────────────────────────────────────────────

@_kitchen_only
def dashboard(request):
    qs = (Order.objects
          .prefetch_related('items__menu_item')
          .select_related('student'))
    return render(request, 'kitchen/dashboard.html', {
        'pending_orders':   qs.filter(status=Order.STATUS_PENDING),
        'preparing_orders': qs.filter(status=Order.STATUS_PREPARING),
        'ready_orders':     qs.filter(status=Order.STATUS_READY),
    })


# ── Status Update (AJAX) ──────────────────────────────────────────────────────

@require_POST
@_kitchen_only
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')
    transitions = {
        Order.STATUS_PENDING:   Order.STATUS_PREPARING,
        Order.STATUS_PREPARING: Order.STATUS_READY,
        Order.STATUS_READY:     Order.STATUS_COMPLETED,
    }
    if new_status == transitions.get(order.status):
        order.status = new_status
        order.save(update_fields=['status', 'updated_at'])
        return JsonResponse({'success': True, 'status': order.status,
                             'status_display': order.get_status_display()})
    return JsonResponse({'success': False, 'error': 'Invalid transition.'}, status=400)
