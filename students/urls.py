"""students/urls.py"""
from django.urls import path
from . import views

urlpatterns = [
    path('login/',                            views.login_view,      name='student_login'),
    path('',                                  views.dashboard,       name='student_dashboard'),
    path('menu/',                             views.menu_view,       name='menu'),
    path('cart/',                             views.cart_view,       name='cart'),
    path('cart/add/',                         views.add_to_cart,     name='add_to_cart'),
    path('cart/update/',                      views.update_cart,     name='update_cart'),
    path('order/place/',                      views.place_order,     name='place_order'),
    path('order/<int:order_id>/status/',      views.order_status,    name='order_status'),
    path('order/<int:order_id>/status/api/',  views.order_status_api,name='order_status_api'),
    path('orders/',                           views.order_history,   name='order_history'),
]
