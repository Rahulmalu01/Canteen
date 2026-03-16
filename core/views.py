"""
core/views.py — All views for the College Canteen Management System
"""

import json
from datetime import date, datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import MenuItemForm, OrderNoteForm, StudentRegistrationForm, StyledAuthForm
from .models import Category, MenuItem, Order, OrderItem, Payment, User


# ─────────────────────────────────────────────
#  Helper decorators
# ─────────────────────────────────────────────

def role_required(*roles):
    """Decorator that ensures the user has one of the specified roles."""
    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles:
                messages.error(request, "You don't have permission to access this page.")
                return redirect('login')
            return view_func(request, *args, **kwargs)
        wrapped_view.__name__ = view_func.__name__
        return wrapped_view
    return decorator


# ─────────────────────────────────────────────
#  Auth Views
# ─────────────────────────────────────────────

def landing_view(request):
    if request.user.is_authenticated:
        return _role_redirect(request.user)
    return redirect('login')


def _role_redirect(user):
    role_map = {
        User.ROLE_STUDENT: 'student_dashboard',
        User.ROLE_KITCHEN: 'kitchen_dashboard',
        User.ROLE_CANTEEN: 'staff_dashboard',
        User.ROLE_ADMIN: 'admin_dashboard',
    }
    return redirect(role_map.get(user.role, 'login'))


def register_view(request):
    if request.user.is_authenticated:
        return _role_redirect(request.user)
    form = StudentRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome, {user.first_name}! Your account has been created.")
        return redirect('student_dashboard')
    return render(request, 'core/auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return _role_redirect(request.user)
    form = StyledAuthForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f"Welcome back, {user.first_name or user.username}!")
        return _role_redirect(user)
    return render(request, 'core/auth/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


# ─────────────────────────────────────────────
#  Student Views
# ─────────────────────────────────────────────

@role_required(User.ROLE_STUDENT)
def student_dashboard(request):
    recent_orders = Order.objects.filter(student=request.user).select_related().prefetch_related('items__menu_item')[:5]
    active_orders = recent_orders.filter(status__in=['pending', 'preparing', 'ready'])
    context = {
        'recent_orders': recent_orders,
        'active_orders': active_orders,
    }
    return render(request, 'core/student/dashboard.html', context)


@role_required(User.ROLE_STUDENT)
def menu_view(request):
    categories = Category.objects.all()
    items = MenuItem.objects.filter(is_available=True).select_related('category')

    # Search
    search = request.GET.get('search', '').strip()
    if search:
        items = items.filter(Q(name__icontains=search) | Q(description__icontains=search))

    # Filter by category
    cat_id = request.GET.get('category')
    if cat_id:
        items = items.filter(category_id=cat_id)

    # Filter veg/non-veg
    veg_filter = request.GET.get('veg')
    if veg_filter == 'veg':
        items = items.filter(is_veg=True)
    elif veg_filter == 'nonveg':
        items = items.filter(is_veg=False)

    # Price range
    max_price = request.GET.get('max_price')
    if max_price:
        try:
            items = items.filter(price__lte=Decimal(max_price))
        except Exception:
            pass

    cart = request.session.get('cart', {})
    context = {
        'categories': categories,
        'items': items,
        'cart': cart,
        'cart_count': sum(cart.values()),
        'search': search,
        'selected_category': cat_id,
        'veg_filter': veg_filter,
        'max_price': max_price,
    }
    return render(request, 'core/student/menu.html', context)


@require_POST
@role_required(User.ROLE_STUDENT)
def add_to_cart(request):
    item_id = str(request.POST.get('item_id'))
    quantity = int(request.POST.get('quantity', 1))
    cart = request.session.get('cart', {})
    cart[item_id] = cart.get(item_id, 0) + quantity
    request.session['cart'] = cart
    return JsonResponse({'success': True, 'cart_count': sum(cart.values())})


@require_POST
@role_required(User.ROLE_STUDENT)
def update_cart(request):
    item_id = str(request.POST.get('item_id'))
    quantity = int(request.POST.get('quantity', 0))
    cart = request.session.get('cart', {})
    if quantity <= 0:
        cart.pop(item_id, None)
    else:
        cart[item_id] = quantity
    request.session['cart'] = cart
    return JsonResponse({'success': True, 'cart_count': sum(cart.values())})


@role_required(User.ROLE_STUDENT)
def cart_view(request):
    cart = request.session.get('cart', {})
    item_ids = [int(k) for k in cart.keys()]
    menu_items = MenuItem.objects.filter(id__in=item_ids)
    cart_items = []
    subtotal = Decimal('0')
    for item in menu_items:
        qty = cart.get(str(item.id), 0)
        line_total = item.price * qty
        subtotal += line_total
        cart_items.append({'item': item, 'quantity': qty, 'line_total': line_total})

    form = OrderNoteForm()
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'form': form,
    }
    return render(request, 'core/student/cart.html', context)


@require_POST
@role_required(User.ROLE_STUDENT)
def place_order(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('cart')

    form = OrderNoteForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Please provide a valid pickup time.")
        return redirect('cart')

    item_ids = [int(k) for k in cart.keys()]
    menu_items = {item.id: item for item in MenuItem.objects.filter(id__in=item_ids)}

    order = Order.objects.create(
        student=request.user,
        pickup_time=form.cleaned_data['pickup_time'],
        notes=form.cleaned_data.get('notes', ''),
        total_amount=0,
    )

    for item_id_str, qty in cart.items():
        item = menu_items.get(int(item_id_str))
        if item:
            OrderItem.objects.create(
                order=order,
                menu_item=item,
                quantity=qty,
                price_at_order=item.price,
            )

    order.calculate_total()

    # Create a mock payment record
    Payment.objects.create(order=order, amount=order.total_amount, status=Payment.STATUS_UNPAID)

    # Clear cart
    request.session['cart'] = {}

    messages.success(request, f"Order #{order.id} placed successfully! Pickup at {form.cleaned_data['pickup_time'].strftime('%I:%M %p')}.")
    return redirect('order_status', order_id=order.id)


@role_required(User.ROLE_STUDENT)
def order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id, student=request.user)
    return render(request, 'core/student/order_status.html', {'order': order})


@require_POST
@role_required(User.ROLE_STUDENT)
def order_status_api(request, order_id):
    """AJAX endpoint to poll current order status."""
    order = get_object_or_404(Order, id=order_id, student=request.user)
    return JsonResponse({'status': order.status, 'status_display': order.get_status_display()})


@role_required(User.ROLE_STUDENT)
def order_history(request):
    orders = Order.objects.filter(student=request.user).prefetch_related('items__menu_item')
    return render(request, 'core/student/order_history.html', {'orders': orders})


# ─────────────────────────────────────────────
#  Kitchen Staff Views
# ─────────────────────────────────────────────

@role_required(User.ROLE_KITCHEN)
def kitchen_dashboard(request):
    pending = Order.objects.filter(status=Order.STATUS_PENDING).prefetch_related('items__menu_item').select_related('student')
    preparing = Order.objects.filter(status=Order.STATUS_PREPARING).prefetch_related('items__menu_item').select_related('student')
    ready = Order.objects.filter(status=Order.STATUS_READY).prefetch_related('items__menu_item').select_related('student')
    context = {
        'pending_orders': pending,
        'preparing_orders': preparing,
        'ready_orders': ready,
    }
    return render(request, 'core/kitchen/dashboard.html', context)


@require_POST
@role_required(User.ROLE_KITCHEN)
def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')
    valid_transitions = {
        Order.STATUS_PENDING: Order.STATUS_PREPARING,
        Order.STATUS_PREPARING: Order.STATUS_READY,
        Order.STATUS_READY: Order.STATUS_COMPLETED,
    }
    if new_status == valid_transitions.get(order.status):
        order.status = new_status
        order.save(update_fields=['status', 'updated_at'])
        return JsonResponse({'success': True, 'status': order.status, 'status_display': order.get_status_display()})
    return JsonResponse({'success': False, 'error': 'Invalid status transition.'}, status=400)


# ─────────────────────────────────────────────
#  Canteen Staff Views
# ─────────────────────────────────────────────

@role_required(User.ROLE_CANTEEN)
def staff_dashboard(request):
    today = date.today()
    daily_orders = Order.objects.filter(created_at__date=today).count()
    daily_revenue = Order.objects.filter(created_at__date=today).aggregate(total=Sum('total_amount'))['total'] or 0
    menu_count = MenuItem.objects.count()
    unavailable_count = MenuItem.objects.filter(is_available=False).count()
    context = {
        'daily_orders': daily_orders,
        'daily_revenue': daily_revenue,
        'menu_count': menu_count,
        'unavailable_count': unavailable_count,
    }
    return render(request, 'core/staff/dashboard.html', context)


@role_required(User.ROLE_CANTEEN)
def menu_management(request):
    items = MenuItem.objects.select_related('category').order_by('category__name', 'name')
    categories = Category.objects.all()
    return render(request, 'core/staff/menu_management.html', {'items': items, 'categories': categories})


@role_required(User.ROLE_CANTEEN)
def add_menu_item(request):
    form = MenuItemForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Menu item added successfully.")
        return redirect('menu_management')
    return render(request, 'core/staff/add_edit_item.html', {'form': form, 'action': 'Add'})


@role_required(User.ROLE_CANTEEN)
def edit_menu_item(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    form = MenuItemForm(request.POST or None, request.FILES or None, instance=item)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"'{item.name}' updated successfully.")
        return redirect('menu_management')
    return render(request, 'core/staff/add_edit_item.html', {'form': form, 'action': 'Edit', 'item': item})


@require_POST
@role_required(User.ROLE_CANTEEN)
def delete_menu_item(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    item.delete()
    messages.success(request, "Item deleted.")
    return redirect('menu_management')


@require_POST
@role_required(User.ROLE_CANTEEN)
def toggle_availability(request, item_id):
    item = get_object_or_404(MenuItem, id=item_id)
    item.is_available = not item.is_available
    item.save(update_fields=['is_available'])
    return JsonResponse({'success': True, 'is_available': item.is_available})


@role_required(User.ROLE_CANTEEN)
def daily_orders_view(request):
    today = date.today()
    orders = (Order.objects
              .filter(created_at__date=today)
              .prefetch_related('items__menu_item')
              .select_related('student'))
    return render(request, 'core/staff/daily_orders.html', {'orders': orders, 'today': today})


# ─────────────────────────────────────────────
#  Admin Views
# ─────────────────────────────────────────────

@role_required(User.ROLE_ADMIN)
def admin_dashboard(request):
    today = date.today()

    # KPI cards
    total_users = User.objects.exclude(role=User.ROLE_ADMIN).count()
    total_orders_today = Order.objects.filter(created_at__date=today).count()
    daily_revenue = Order.objects.filter(created_at__date=today).aggregate(t=Sum('total_amount'))['t'] or 0
    pending_orders = Order.objects.filter(status=Order.STATUS_PENDING).count()

    # Revenue last 7 days for Chart.js
    revenue_data = []
    labels = []
    for i in range(6, -1, -1):
        from datetime import timedelta
        day = today - timedelta(days=i)
        rev = Order.objects.filter(created_at__date=day).aggregate(t=Sum('total_amount'))['t'] or 0
        revenue_data.append(float(rev))
        labels.append(day.strftime('%d %b'))

    # Top 5 popular items
    top_items = (OrderItem.objects
                 .values('menu_item__name')
                 .annotate(total_qty=Sum('quantity'))
                 .order_by('-total_qty')[:5])
    top_labels = [i['menu_item__name'] for i in top_items]
    top_data = [i['total_qty'] for i in top_items]

    # Orders by status
    status_counts = {s: Order.objects.filter(status=s).count() for s, _ in Order.STATUS_CHOICES}

    context = {
        'total_users': total_users,
        'total_orders_today': total_orders_today,
        'daily_revenue': daily_revenue,
        'pending_orders': pending_orders,
        'revenue_labels': json.dumps(labels),
        'revenue_data': json.dumps(revenue_data),
        'top_labels': json.dumps(top_labels),
        'top_data': json.dumps(top_data),
        'status_counts': status_counts,
    }
    return render(request, 'core/admin_panel/dashboard.html', context)


@role_required(User.ROLE_ADMIN)
def admin_user_management(request):
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'core/admin_panel/users.html', {'users': users})


@require_POST
@role_required(User.ROLE_ADMIN)
def admin_change_role(request, user_id):
    user = get_object_or_404(User, id=user_id)
    new_role = request.POST.get('role')
    if new_role in dict(User.ROLE_CHOICES):
        user.role = new_role
        user.save(update_fields=['role'])
        messages.success(request, f"{user.username}'s role changed to {user.get_role_display()}.")
    return redirect('admin_user_management')


@role_required(User.ROLE_ADMIN)
def admin_all_orders(request):
    orders = Order.objects.all().select_related('student').prefetch_related('items__menu_item')
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'core/admin_panel/orders.html', context)
