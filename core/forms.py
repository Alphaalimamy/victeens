from django import forms
from .models import ContactMessage

class ContactForm(forms.ModelForm):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'Your full name'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'input-field',
            'placeholder': 'your@email.com'
        })
    )
    
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': '+254 712 345 678 (optional)'
        })
    )
    
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'What is this regarding?'
        })
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'input-field',
            'rows': 5,
            'placeholder': 'Your message...'
        })
    )
    
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']