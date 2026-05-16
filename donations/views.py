from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
import json

from .models import Donation, DonationCampaign, DonationCategory, ImpactReport, RecurringDonation
from .forms import DonationForm, MpesaPaymentForm, CardPaymentForm, BankTransferForm

def donation_home(request):
    """Main donation page"""
    campaigns = DonationCampaign.objects.filter(is_active=True, is_featured=True)[:3]
    categories = DonationCategory.objects.filter(is_active=True)
    impact_reports = ImpactReport.objects.filter(is_active=True)
    
    # Calculate total donations (simplified - will be improved)
    total_donations = Donation.objects.filter(payment_status='completed').count()
    
    context = {
        'title': 'Donate',
        'campaigns': campaigns,
        'categories': categories,
        'impact_reports': impact_reports,
        'total_donations': total_donations,
    }
    return render(request, 'donations/home.html', context)


def donation_campaigns(request):
    """List all active campaigns"""
    campaigns = DonationCampaign.objects.filter(is_active=True).order_by('-is_featured', '-start_date')
    
    context = {
        'title': 'Campaigns',
        'campaigns': campaigns,
    }
    return render(request, 'donations/campaigns.html', context)


def campaign_detail(request, slug):
    """Campaign detail page"""
    campaign = get_object_or_404(DonationCampaign, slug=slug, is_active=True)
    recent_donations = Donation.objects.filter(
        campaign=campaign, 
        payment_status='completed',
        is_anonymous=False
    ).select_related('donor')[:10]
    
    context = {
        'title': campaign.title,
        'campaign': campaign,
        'recent_donations': recent_donations,
    }
    return render(request, 'donations/campaign_detail.html', context)


@login_required
def make_donation(request):
    """Make a donation"""
    if request.method == 'POST':
        form = DonationForm(request.POST, request=request)
        
        if form.is_valid():
            donation = form.save(commit=False)
            
            # Set donor for authenticated users
            if request.user.is_authenticated and not form.cleaned_data['guest_donor']:
                donation.donor = request.user
                donation.guest_donor = False
            
            # Set initial payment status
            donation.payment_status = 'pending'
            donation.currency = 'Le'
            donation.ip_address = request.META.get('REMOTE_ADDR')
            donation.user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Check if recurring
            donation_type = form.cleaned_data['donation_type']
            donation.is_recurring = donation_type != 'one_time'
            
            donation.save()
            
            # Store donation ID in session for payment processing
            request.session['donation_id'] = donation.id
            request.session['payment_method'] = form.cleaned_data['payment_method']
            
            # Redirect to payment page
            return redirect('donations:payment', donation_id=donation.donation_id)
    
    else:
        form = DonationForm(request=request)
    
    campaigns = DonationCampaign.objects.filter(is_active=True)
    impact_reports = ImpactReport.objects.filter(is_active=True)
    
    context = {
        'title': 'Make a Donation',
        'form': form,
        'campaigns': campaigns,
        'impact_reports': impact_reports,
    }
    return render(request, 'donations/make_donation.html', context)


def donation_payment(request, donation_id):
    """Payment processing page"""
    donation = get_object_or_404(Donation, donation_id=donation_id)
    
    # Check if donation belongs to user or is in session
    if (donation.donor != request.user and 
        request.session.get('donation_id') != donation.id):
        messages.error(request, 'You are not authorized to access this payment.')
        return redirect('donations:home')
    
    # Initialize payment form based on method
    payment_method = donation.payment_method
    payment_form = None
    
    if payment_method == 'mpesa':
        payment_form = MpesaPaymentForm()
    elif payment_method == 'stripe':
        payment_form = CardPaymentForm()
    elif payment_method == 'bank_transfer':
        payment_form = BankTransferForm()
    
    if request.method == 'POST':
        if payment_method == 'mpesa':
            payment_form = MpesaPaymentForm(request.POST)
            if payment_form.is_valid():
                # Process M-Pesa payment (simulated for now)
                phone_number = payment_form.cleaned_data['phone_number']
                
                # Simulate payment processing
                donation.transaction_id = f"MPESA{timezone.now().strftime('%Y%m%d%H%M%S')}"
                donation.payment_status = 'completed'
                donation.save()
                
                # Send payment confirmation
                send_donation_confirmation(donation, phone_number)
                
                messages.success(request, 'Payment initiated! Check your phone to complete the M-Pesa transaction.')
                return redirect('donations:success', donation_id=donation.donation_id)
        
        elif payment_method == 'stripe':
            payment_form = CardPaymentForm(request.POST)
            if payment_form.is_valid():
                # Process card payment (simulated)
                donation.transaction_id = f"STRIPE{timezone.now().strftime('%Y%m%d%H%M%S')}"
                donation.payment_status = 'completed'
                donation.save()
                
                messages.success(request, 'Payment processed successfully!')
                return redirect('donations:success', donation_id=donation.donation_id)
        
        elif payment_method == 'bank_transfer':
            payment_form = BankTransferForm(request.POST, request.FILES)
            if payment_form.is_valid():
                # Store bank transfer details
                donation.transaction_id = payment_form.cleaned_data['reference_number']
                donation.notes = f"Bank transfer on {payment_form.cleaned_data['transfer_date']}"
                donation.payment_status = 'pending'  # Needs verification
                donation.save()
                
                messages.success(
                    request, 
                    'Thank you! We will verify your bank transfer within 24 hours.'
                )
                return redirect('donations:pending', donation_id=donation.donation_id)
    
    context = {
        'title': 'Complete Payment',
        'donation': donation,
        'payment_form': payment_form,
        'payment_method': payment_method,
    }
    return render(request, 'donations/payment.html', context)


def donation_success(request, donation_id):
    """Donation success page"""
    donation = get_object_or_404(Donation, donation_id=donation_id)
    
    # Check authorization
    if (donation.donor != request.user and 
        request.session.get('donation_id') != donation.id):
        messages.error(request, 'You are not authorized to view this page.')
        return redirect('donations:home')
    
    # Clear session data
    if 'donation_id' in request.session:
        del request.session['donation_id']
    if 'payment_method' in request.session:
        del request.session['payment_method']
    
    # Generate receipt (simplified)
    receipt_number = donation.receipt_number
    
    context = {
        'title': 'Donation Successful',
        'donation': donation,
        'receipt_number': receipt_number,
    }
    return render(request, 'donations/success.html', context)


def donation_pending(request, donation_id):
    """Pending donation page (for bank transfers)"""
    donation = get_object_or_404(Donation, donation_id=donation_id)
    
    context = {
        'title': 'Donation Pending Verification',
        'donation': donation,
    }
    return render(request, 'donations/pending.html', context)


@login_required
def donation_history(request):
    """User's donation history"""
    donations = Donation.objects.filter(donor=request.user).order_by('-created_at')
    recurring = RecurringDonation.objects.filter(donor=request.user, status='active')
    
    # Calculate totals
    total_donated = sum(d.amount for d in donations.filter(payment_status='completed'))
    total_donations = donations.filter(payment_status='completed').count()
    
    context = {
        'title': 'My Donations',
        'donations': donations,
        'recurring_donations': recurring,
        'total_donated': total_donated,
        'total_donations': total_donations,
    }
    return render(request, 'donations/history.html', context)


@login_required
def donation_detail(request, donation_id):
    """Detailed view of a single donation"""
    donation = get_object_or_404(Donation, donation_id=donation_id, donor=request.user)
    
    context = {
        'title': f'Donation {donation.donation_id}',
        'donation': donation,
    }
    return render(request, 'donations/detail.html', context)


@login_required
def manage_recurring(request, subscription_id):
    """Manage recurring donation"""
    recurring = get_object_or_404(RecurringDonation, subscription_id=subscription_id, donor=request.user)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'cancel':
            recurring.status = 'cancelled'
            recurring.save()
            messages.success(request, 'Your recurring donation has been cancelled.')
        elif action == 'pause':
            recurring.status = 'paused'
            recurring.save()
            messages.success(request, 'Your recurring donation has been paused.')
        elif action == 'resume':
            recurring.status = 'active'
            recurring.save()
            messages.success(request, 'Your recurring donation has been resumed.')
        
        return redirect('donations:history')
    
    context = {
        'title': 'Manage Recurring Donation',
        'recurring': recurring,
    }
    return render(request, 'donations/manage_recurring.html', context)


def send_donation_confirmation(donation, phone_number=None):
    """Send donation confirmation email/SMS"""
    # Email confirmation
    if donation.donor_email:
        subject = f'Thank you for your donation to Victory Teens!'
        html_message = render_to_string('donations/emails/donation_confirmation.html', {
            'donation': donation,
            'receipt_number': donation.receipt_number,
        })
        
        send_mail(
            subject=subject,
            message='',  # Plain text version would go here
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[donation.donor_email],
            fail_silently=True,
        )
        
        donation.receipt_sent = True
        donation.receipt_sent_at = timezone.now()
        donation.save()
    
    # SMS confirmation (simulated)
    if phone_number:
        # In production, integrate with SMS gateway like Africa's Talking
        print(f"SMS would be sent to {phone_number}: Thank you for your donation of KES {donation.amount} to Victory Teens.")


@csrf_exempt
@require_POST
def mpesa_webhook(request):
    """Handle M-Pesa payment webhooks (simplified)"""
    # This would integrate with M-Pesa API in production
    try:
        data = json.loads(request.body)
        # Process webhook data
        # Update donation status based on M-Pesa callback
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe payment webhooks (simplified)"""
    try:
        data = json.loads(request.body)
        # Process Stripe webhook
        # Update donation status based on Stripe events
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)