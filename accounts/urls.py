"""accounts/urls.py"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]
