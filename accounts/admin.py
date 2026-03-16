"""
accounts/admin.py — Register all models with Django admin
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Category, MenuItem, Order, OrderItem, Payment


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Contact', {'fields': ('role', 'phone', 'profile_pic')}),
    )
    list_display  = ('username', 'email', 'get_role_display', 'is_active', 'date_joined')
    list_filter   = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'icon')
    search_fields = ('name',)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display   = ('name', 'category', 'price', 'is_veg', 'is_available')
    list_filter    = ('category', 'is_veg', 'is_available')
    search_fields  = ('name',)
    list_editable  = ('price', 'is_available')


class OrderItemInline(admin.TabularInline):
    model      = OrderItem
    extra      = 0
    readonly_fields = ('price_at_order',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ('id', 'student', 'status', 'total_amount', 'pickup_time', 'created_at')
    list_filter   = ('status', 'created_at')
    search_fields = ('student__username',)
    inlines       = [OrderItemInline]
    readonly_fields = ('total_amount', 'created_at', 'updated_at')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ('order', 'amount', 'status', 'transaction_id', 'paid_at')
    list_filter   = ('status',)
    search_fields = ('order__id', 'transaction_id')
