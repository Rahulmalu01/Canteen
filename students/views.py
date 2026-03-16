"""students/views.py — Student login + all student-facing views"""

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.forms import RoleLoginForm, StudentRegistrationForm, OrderNoteForm
from accounts.models import User, Category, MenuItem, Order, OrderItem, Payment


# ── Helpers ──────────────────────────────────────────────────────────────────

def _student_only(view_fn):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != User.ROLE_STUDENT:
            messages.error(request, "Please log in as a Student.")
            return redirect('student_login')
        return view_fn(request, *args, **kwargs)
    wrapper.__name__ = view_fn.__name__
    return wrapper


# ── Auth ─────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated and request.user.role == User.ROLE_STUDENT:
        return redirect('student_dashboard')

    form = RoleLoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if user.role != User.ROLE_STUDENT:
            messages.error(request, "⛔ This portal is for Students only. Use the correct login page.")
        else:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('student_dashboard')
    return render(request, 'students/login.html', {'form': form})


# ── Dashboard ────────────────────────────────────────────────────────────────

@_student_only
def dashboard(request):
    orders = (Order.objects.filter(student=request.user)
              .prefetch_related('items__menu_item')[:6])
    active = [o for o in orders if o.status in ('pending', 'preparing', 'ready')]
    return render(request, 'students/dashboard.html', {
        'recent_orders': orders,
        'active_orders': active,
    })


# ── Menu ─────────────────────────────────────────────────────────────────────

@_student_only
def menu_view(request):
    categories = Category.objects.all()
    items = MenuItem.objects.filter(is_available=True).select_related('category')

    search = request.GET.get('search', '').strip()
    if search:
        items = items.filter(Q(name__icontains=search) | Q(description__icontains=search))

    cat_id = request.GET.get('category')
    if cat_id:
        items = items.filter(category_id=cat_id)

    veg_filter = request.GET.get('veg')
    if veg_filter == 'veg':
        items = items.filter(is_veg=True)
    elif veg_filter == 'nonveg':
        items = items.filter(is_veg=False)

    max_price = request.GET.get('max_price')
    if max_price:
        try:
            items = items.filter(price__lte=Decimal(max_price))
        except Exception:
            pass

    cart = request.session.get('cart', {})
    return render(request, 'students/menu.html', {
        'categories': categories,
        'items': items,
        'cart_count': sum(cart.values()),
        'search': search,
        'selected_category': cat_id,
        'veg_filter': veg_filter,
        'max_price': max_price,
    })


# ── Cart AJAX ────────────────────────────────────────────────────────────────

@require_POST
@_student_only
def add_to_cart(request):
    item_id  = str(request.POST.get('item_id'))
    quantity = int(request.POST.get('quantity', 1))
    cart = request.session.get('cart', {})
    cart[item_id] = cart.get(item_id, 0) + quantity
    request.session['cart'] = cart
    return JsonResponse({'success': True, 'cart_count': sum(cart.values())})


@require_POST
@_student_only
def update_cart(request):
    item_id  = str(request.POST.get('item_id'))
    quantity = int(request.POST.get('quantity', 0))
    cart = request.session.get('cart', {})
    if quantity <= 0:
        cart.pop(item_id, None)
    else:
        cart[item_id] = quantity
    request.session['cart'] = cart
    return JsonResponse({'success': True, 'cart_count': sum(cart.values())})


# ── Cart Page ────────────────────────────────────────────────────────────────

@_student_only
def cart_view(request):
    cart = request.session.get('cart', {})
    item_ids = [int(k) for k in cart]
    menu_items = MenuItem.objects.filter(id__in=item_ids)
    cart_items, subtotal = [], Decimal('0')
    for item in menu_items:
        qty = cart.get(str(item.id), 0)
        line = item.price * qty
        subtotal += line
        cart_items.append({'item': item, 'quantity': qty, 'line_total': line})
    return render(request, 'students/cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'form': OrderNoteForm(),
    })


# ── Place Order ──────────────────────────────────────────────────────────────

@require_POST
@_student_only
def place_order(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('cart')

    form = OrderNoteForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Please provide a valid pickup time.")
        return redirect('cart')

    item_ids   = [int(k) for k in cart]
    menu_items = {m.id: m for m in MenuItem.objects.filter(id__in=item_ids)}

    order = Order.objects.create(
        student=request.user,
        pickup_time=form.cleaned_data['pickup_time'],
        notes=form.cleaned_data.get('notes', ''),
        total_amount=0,
    )
    for id_str, qty in cart.items():
        item = menu_items.get(int(id_str))
        if item:
            OrderItem.objects.create(
                order=order, menu_item=item,
                quantity=qty, price_at_order=item.price,
            )

    order.calculate_total()
    Payment.objects.create(order=order, amount=order.total_amount,
                           status=Payment.STATUS_UNPAID)
    request.session['cart'] = {}
    messages.success(request, f"✅ Order #{order.id} placed! Pickup at {form.cleaned_data['pickup_time'].strftime('%I:%M %p')}.")
    return redirect('order_status', order_id=order.id)


# ── Order Status ─────────────────────────────────────────────────────────────

@_student_only
def order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id, student=request.user)
    return render(request, 'students/order_status.html', {'order': order})


@require_POST
@_student_only
def order_status_api(request, order_id):
    order = get_object_or_404(Order, id=order_id, student=request.user)
    return JsonResponse({'status': order.status,
                         'status_display': order.get_status_display()})


# ── Order History ────────────────────────────────────────────────────────────

@_student_only
def order_history(request):
    orders = (Order.objects.filter(student=request.user)
              .prefetch_related('items__menu_item'))
    return render(request, 'students/order_history.html', {'orders': orders})
