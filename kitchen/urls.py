"""kitchen/urls.py"""
from django.urls import path
from . import views

urlpatterns = [
    path('login/',                          views.login_view,         name='kitchen_login'),
    path('',                                views.dashboard,          name='kitchen_dashboard'),
    path('order/<int:order_id>/update/',    views.update_order_status,name='update_order_status'),
]
