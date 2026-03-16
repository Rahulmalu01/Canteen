"""
accounts/models.py — All shared database models (single source of truth)
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_STUDENT = 'student'
    ROLE_KITCHEN = 'kitchen_staff'
    ROLE_CANTEEN = 'canteen_staff'
    ROLE_ADMIN   = 'admin'

    ROLE_CHOICES = [
        (ROLE_STUDENT, 'Student'),
        (ROLE_KITCHEN, 'Kitchen Staff'),
        (ROLE_CANTEEN, 'Canteen Staff'),
        (ROLE_ADMIN,   'Admin'),
    ]

    role  = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    phone = models.CharField(max_length=15, blank=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)

    # Convenience helpers
    def is_student(self):       return self.role == self.ROLE_STUDENT
    def is_kitchen_staff(self): return self.role == self.ROLE_KITCHEN
    def is_canteen_staff(self): return self.role == self.ROLE_CANTEEN
    def is_admin_user(self):    return self.role == self.ROLE_ADMIN

    def get_dashboard_url(self):
        from django.urls import reverse
        mapping = {
            self.ROLE_STUDENT: 'student_dashboard',
            self.ROLE_KITCHEN: 'kitchen_dashboard',
            self.ROLE_CANTEEN: 'staff_dashboard',
            self.ROLE_ADMIN:   'admin_dashboard',
        }
        return reverse(mapping.get(self.role, 'landing'))

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=60, blank=True,
                            help_text="Bootstrap icon name e.g. bi-cup-hot")

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category    = models.ForeignKey(Category, on_delete=models.SET_NULL,
                                    null=True, related_name='items')
    name        = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price       = models.DecimalField(max_digits=8, decimal_places=2)
    image       = models.ImageField(upload_to='menu/', blank=True, null=True)
    is_veg      = models.BooleanField(default=True)
    is_available = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} (₹{self.price})"


class Order(models.Model):
    STATUS_PENDING   = 'pending'
    STATUS_PREPARING = 'preparing'
    STATUS_READY     = 'ready'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING,   'Pending'),
        (STATUS_PREPARING, 'Preparing'),
        (STATUS_READY,     'Ready for Pickup'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    student      = models.ForeignKey(User, on_delete=models.CASCADE,
                                     related_name='orders')
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                    default=STATUS_PENDING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pickup_time  = models.TimeField()
    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} — {self.student.username} [{self.get_status_display()}]"

    def calculate_total(self):
        self.total_amount = sum(item.subtotal() for item in self.items.all())
        self.save(update_fields=['total_amount'])


class OrderItem(models.Model):
    order          = models.ForeignKey(Order, on_delete=models.CASCADE,
                                       related_name='items')
    menu_item      = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity       = models.PositiveIntegerField(default=1)
    price_at_order = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ('order', 'menu_item')

    def subtotal(self):
        return self.price_at_order * self.quantity

    def __str__(self):
        return f"{self.quantity}× {self.menu_item.name} (Order #{self.order.id})"


class Payment(models.Model):
    STATUS_PAID     = 'paid'
    STATUS_UNPAID   = 'unpaid'
    STATUS_REFUNDED = 'refunded'

    STATUS_CHOICES = [
        (STATUS_PAID,     'Paid'),
        (STATUS_UNPAID,   'Unpaid'),
        (STATUS_REFUNDED, 'Refunded'),
    ]

    order          = models.OneToOneField(Order, on_delete=models.CASCADE,
                                          related_name='payment')
    amount         = models.DecimalField(max_digits=10, decimal_places=2)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES,
                                      default=STATUS_UNPAID)
    transaction_id = models.CharField(max_length=100, blank=True)
    paid_at        = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment for Order #{self.order.id} — {self.get_status_display()}"
