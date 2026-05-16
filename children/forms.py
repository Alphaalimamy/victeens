from django import forms
from .models import Sponsorship, Child

class ChildSearchForm(forms.Form):
    """Form for searching children"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'Search by name, interests, or background...'
        })
    )
    
    category = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'input-field'})
    )
    
    min_age = forms.IntegerField(
        required=False,
        min_value=13,
        max_value=19,
        widget=forms.NumberInput(attrs={
            'class': 'input-field',
            'placeholder': 'Min age',
            'min': '13',
            'max': '19'
        })
    )
    
    max_age = forms.IntegerField(
        required=False,
        min_value=13,
        max_value=19,
        widget=forms.NumberInput(attrs={
            'class': 'input-field',
            'placeholder': 'Max age',
            'min': '13',
            'max': '19'
        })
    )
    
    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ('display_order', 'Recommended'),
            ('age', 'Age (Youngest First)'),
            ('newest', 'Newest Arrivals'),
            ('urgent', 'Most Urgent'),
        ],
        widget=forms.Select(attrs={'class': 'input-field'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import ChildCategory
        categories = ChildCategory.objects.filter(is_active=True)
        self.fields['category'].choices = [('', 'All Categories')] + [
            (cat.slug, cat.name) for cat in categories
        ]


class ChildSponsorshipForm(forms.ModelForm):
    """Form for starting child sponsorship"""
    SPONSORSHIP_TYPES = [
        ('full', 'Full Sponsorship - KES 10,000/month'),
        ('partial', 'Partial Sponsorship - KES 5,000/month'),
        ('education', 'Education Only - KES 3,000/month'),
        ('health', 'Healthcare Only - KES 2,000/month'),
    ]
    
    PAYMENT_METHODS = [
        ('mpesa', 'M-Pesa - Mobile Money'),
        ('stripe', 'Credit/Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    COMMUNICATION_FREQUENCIES = [
        ('weekly', 'Weekly Updates'),
        ('monthly', 'Monthly Updates'),
        ('quarterly', 'Quarterly Updates'),
        ('biannual', 'Twice a Year'),
    ]
    
    sponsorship_type = forms.ChoiceField(
        choices=SPONSORSHIP_TYPES,
        widget=forms.RadioSelect(attrs={'class': 'hidden'}),
        initial='partial'
    )
    
    communication_frequency = forms.ChoiceField(
        choices=COMMUNICATION_FREQUENCIES,
        widget=forms.RadioSelect(attrs={'class': 'hidden'}),
        initial='monthly'
    )
    
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHODS,
        widget=forms.RadioSelect(attrs={'class': 'hidden'}),
        initial='mpesa'
    )
    
    personal_message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'input-field',
            'rows': 4,
            'placeholder': 'Optional: Write a brief message to the child...'
        })
    )
    
    agree_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-vto-orange-dark rounded'})
    )
    
    class Meta:
        model = Sponsorship
        fields = ['sponsorship_type', 'communication_frequency', 'payment_method']
    
    def __init__(self, *args, **kwargs):
        self.child = kwargs.pop('child', None)
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set initial monthly amount based on sponsorship type
        if 'sponsorship_type' in self.data:
            sponsorship_type = self.data['sponsorship_type']
        else:
            sponsorship_type = self.initial.get('sponsorship_type', 'partial')
        
        amount_map = {
            'full': 10000,
            'partial': 5000,
            'education': 3000,
            'health': 2000,
        }
        
        self.initial['monthly_amount'] = amount_map.get(sponsorship_type, 5000)
    
    def clean(self):
        cleaned_data = super().clean()
        sponsorship_type = cleaned_data.get('sponsorship_type')
        
        # Set monthly amount based on type
        amount_map = {
            'full': 10000,
            'partial': 5000,
            'education': 3000,
            'health': 2000,
        }
        
        cleaned_data['monthly_amount'] = amount_map.get(sponsorship_type, 5000)
        
        return cleaned_data


class ChildMessageForm(forms.Form):
    """Form for sending messages to sponsored children"""
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'Message subject...'
        })
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'input-field',
            'rows': 6,
            'placeholder': 'Write your message here...'
        })
    )
    
    include_photo = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-vto-orange-dark rounded'})
    )
    
    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'input-field',
            'accept': 'image/*'
        })
    )


class ChildUpdateForm(forms.Form):
    """Form for submitting updates about sponsored children"""
    update_type = forms.ChoiceField(
        choices=[
            ('progress', 'Progress Report'),
            ('academic', 'Academic Achievement'),
            ('personal', 'Personal Growth'),
            ('health', 'Health Update'),
            ('event', 'Special Event'),
        ],
        widget=forms.Select(attrs={'class': 'input-field'})
    )
    
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'Update title...'
        })
    )
    
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'input-field',
            'rows': 8,
            'placeholder': 'Write the update here...'
        })
    )
    
    photos = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'input-field',
            'multiple': True,
            'accept': 'image/*'
        })
    )
    
    can_share_publicly = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-vto-orange-dark rounded'})
    )