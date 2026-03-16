"""
core/urls.py — URL routing for all canteen app views
"""

from django.urls import path
from . import views

urlpatterns = [
    # ── Landing ──────────────────────────────────────────────────────────────
    path('', views.landing_view, name='landing'),

    # ── Auth ─────────────────────────────────────────────────────────────────
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ── Student ───────────────────────────────────────────────────────────────
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/menu/', views.menu_view, name='menu'),
    path('student/cart/', views.cart_view, name='cart'),
    path('student/cart/add/', views.add_to_cart, name='add_to_cart'),
    path('student/cart/update/', views.update_cart, name='update_cart'),
    path('student/order/place/', views.place_order, name='place_order'),
    path('student/order/<int:order_id>/status/', views.order_status, name='order_status'),
    path('student/order/<int:order_id>/status/api/', views.order_status_api, name='order_status_api'),
    path('student/orders/', views.order_history, name='order_history'),

    # ── Kitchen Staff ─────────────────────────────────────────────────────────
    path('kitchen/', views.kitchen_dashboard, name='kitchen_dashboard'),
    path('kitchen/order/<int:order_id>/update/', views.update_order_status, name='update_order_status'),

    # ── Canteen Staff ─────────────────────────────────────────────────────────
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/menu/', views.menu_management, name='menu_management'),
    path('staff/menu/add/', views.add_menu_item, name='add_menu_item'),
    path('staff/menu/<int:item_id>/edit/', views.edit_menu_item, name='edit_menu_item'),
    path('staff/menu/<int:item_id>/delete/', views.delete_menu_item, name='delete_menu_item'),
    path('staff/menu/<int:item_id>/toggle/', views.toggle_availability, name='toggle_availability'),
    path('staff/daily-orders/', views.daily_orders_view, name='daily_orders'),

    # ── Admin ─────────────────────────────────────────────────────────────────
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/users/', views.admin_user_management, name='admin_user_management'),
    path('admin-panel/users/<int:user_id>/role/', views.admin_change_role, name='admin_change_role'),
    path('admin-panel/orders/', views.admin_all_orders, name='admin_all_orders'),
]
