"""canteen_staff/urls.py"""
from django.urls import path
from . import views

urlpatterns = [
    path('login/',                          views.login_view,        name='staff_login'),
    path('',                                views.dashboard,         name='staff_dashboard'),
    path('menu/',                           views.menu_management,   name='menu_management'),
    path('menu/add/',                       views.add_menu_item,     name='add_menu_item'),
    path('menu/<int:item_id>/edit/',        views.edit_menu_item,    name='edit_menu_item'),
    path('menu/<int:item_id>/delete/',      views.delete_menu_item,  name='delete_menu_item'),
    path('menu/<int:item_id>/toggle/',      views.toggle_availability,name='toggle_availability'),
    path('daily-orders/',                   views.daily_orders,      name='daily_orders'),
]
