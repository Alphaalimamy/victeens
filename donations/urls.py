from django.urls import path
from . import views

app_name = 'donations'

urlpatterns = [
    # Main donation pages
    path('donations/', views.donation_home, name='donations'),
    path('campaigns/', views.donation_campaigns, name='campaigns'),
    path('campaigns/<slug:slug>/', views.campaign_detail, name='campaign_detail'),
    
    # Donation process
    path('make-donation/', views.make_donation, name='make_donation'),
    path('payment/<str:donation_id>/', views.donation_payment, name='payment'),
    path('success/<str:donation_id>/', views.donation_success, name='success'),
    path('pending/<str:donation_id>/', views.donation_pending, name='pending'),
    
    # User donation management
    path('my-donations/', views.donation_history, name='my_donations'),
    path('donation/<str:donation_id>/', views.donation_detail, name='detail'),
    path('recurring/<str:subscription_id>/manage/', views.manage_recurring, name='manage_recurring'),
    
    # Webhooks (for production)
    path('webhook/mpesa/', views.mpesa_webhook, name='mpesa_webhook'),
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
]