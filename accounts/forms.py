"""
accounts/forms.py — Shared forms (student registration, role-aware login)
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, MenuItem, Order


# ── Student Registration ────────────────────────────────────────────────────

class StudentRegistrationForm(UserCreationForm):
    email      = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50, required=True)
    last_name  = forms.CharField(max_length=50, required=True)
    phone      = forms.CharField(max_length=15, required=False)

    class Meta:
        model  = User
        fields = ('username', 'first_name', 'last_name', 'email', 'phone',
                  'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role  = User.ROLE_STUDENT
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


# ── Styled Login (base for each role app) ──────────────────────────────────

class RoleLoginForm(AuthenticationForm):
    """AuthenticationForm pre-wired with Bootstrap classes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control', 'autocomplete': 'on'})


# ── Menu Item Form (used by canteen_staff app) ──────────────────────────────

class MenuItemForm(forms.ModelForm):
    class Meta:
        model  = MenuItem
        fields = ('name', 'category', 'description', 'price',
                  'image', 'is_veg', 'is_available')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:
                field.widget.attrs.update({'class': 'form-control'})


# ── Order Pickup / Notes Form (used by students app) ───────────────────────

class OrderNoteForm(forms.ModelForm):
    class Meta:
        model  = Order
        fields = ('pickup_time', 'notes')
        widgets = {
            'pickup_time': forms.TimeInput(
                attrs={'type': 'time', 'class': 'form-control'}),
            'notes': forms.Textarea(
                attrs={'rows': 2, 'class': 'form-control',
                       'placeholder': 'Any special instructions?'}),
        }
