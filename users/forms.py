from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.exceptions import ValidationError
from .models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'input-field',
        'placeholder': 'your@email.com'
    }))
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'role')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input-field'}),
            'last_name': forms.TextInput(attrs={'class': 'input-field'}),
            'phone': forms.TextInput(attrs={'class': 'input-field', 'placeholder': '+23277000000'}),
            'role': forms.Select(attrs={'class': 'input-field'}),
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'role', 'avatar', 'bio')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'phone', 'avatar', 'bio', 
                  'address', 'city', 'country', 'date_of_birth',
                  'newsletter_subscription', 'email_notifications')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input-field'}),
            'last_name': forms.TextInput(attrs={'class': 'input-field'}),
            'phone': forms.TextInput(attrs={'class': 'input-field'}),
            'bio': forms.Textarea(attrs={'class': 'input-field', 'rows': 4}),
            'address': forms.Textarea(attrs={'class': 'input-field', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'input-field'}),
            'country': forms.TextInput(attrs={'class': 'input-field'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'input-field', 'type': 'date'}),
        }


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'input-field',
            'placeholder': 'your@email.com'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input-field',
            'placeholder': 'Enter your password'
        })
    )
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-vto-orange-dark rounded'})
    )