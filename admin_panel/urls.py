"""admin_panel/urls.py"""
from django.urls import path
from . import views

urlpatterns = [
    path('login/',                          views.login_view,    name='admin_login'),
    path('',                                views.dashboard,     name='admin_dashboard'),
    path('users/',                          views.user_management,name='admin_user_management'),
    path('users/<int:user_id>/role/',       views.change_role,   name='admin_change_role'),
    path('orders/',                         views.all_orders,    name='admin_all_orders'),
]
