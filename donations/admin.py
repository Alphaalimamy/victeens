from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import (
    DonationCategory, DonationCampaign, Donation, 
    RecurringDonation, DonationReceipt, ImpactReport
)

@admin.register(DonationCategory)
class DonationCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'is_active', 'order']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']


@admin.register(DonationCampaign)
class DonationCampaignAdmin(admin.ModelAdmin):
    list_display = ['title', 'goal_amount', 'current_amount', 'progress_bar', 
                   'is_featured', 'is_active', 'start_date']
    list_editable = ['is_featured', 'is_active']
    list_filter = ['is_featured', 'is_active', 'start_date']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    
    def progress_bar(self, obj):
        progress = obj.progress_percentage
        color = 'green' if progress >= 100 else 'orange' if progress >= 50 else 'red'
        return format_html(
            '<div style="width: 100px; background-color: #e0e0e0; border-radius: 3px;">'
            '<div style="width: {}%; height: 20px; background-color: {}; border-radius: 3px; text-align: center; color: white; font-size: 12px; line-height: 20px;">{}%</div>'
            '</div>',
            progress, color, int(progress)
        )
    progress_bar.short_description = 'Progress'


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ['donation_id', 'donor_name', 'amount', 'currency', 
                   'payment_status', 'payment_method', 'created_at']
    list_filter = ['payment_status', 'payment_method', 'donation_type', 
                  'is_recurring', 'created_at', 'campaign']
    search_fields = ['donation_id', 'donor_name', 'donor_email', 
                    'transaction_id', 'donor__email']
    readonly_fields = ['donation_id', 'created_at', 'updated_at', 
                      'ip_address', 'user_agent']
    list_per_page = 50
    
    fieldsets = [
        ('Donation Information', {
            'fields': ['donation_id', 'amount', 'currency', 'donation_type', 
                      'category', 'campaign', 'is_recurring']
        }),
        ('Donor Information', {
            'fields': ['donor', 'guest_donor', 'donor_name', 'donor_email', 
                      'donor_phone', 'is_anonymous', 'is_dedicated', 
                      'dedication_name', 'dedication_message']
        }),
        ('Payment Information', {
            'fields': ['payment_method', 'transaction_id', 'payment_status',
                      'recurring_id', 'next_payment_date', 'recurring_end_date']
        }),
        ('Receipt Information', {
            'fields': ['receipt_sent', 'receipt_sent_at', 'notes']
        }),
        ('Metadata', {
            'fields': ['ip_address', 'user_agent', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    actions = ['mark_as_completed', 'mark_as_refunded', 'send_receipts']
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(payment_status='completed')
        self.message_user(request, f"{updated} donations marked as completed.")
    mark_as_completed.short_description = "Mark selected donations as completed"
    
    def mark_as_refunded(self, request, queryset):
        updated = queryset.update(payment_status='refunded')
        self.message_user(request, f"{updated} donations marked as refunded.")
    mark_as_refunded.short_description = "Mark selected donations as refunded"
    
    def send_receipts(self, request, queryset):
        # In production, this would send emails
        self.message_user(request, "Receipt sending functionality will be implemented in production.")
    send_receipts.short_description = "Send receipts for selected donations"


@admin.register(RecurringDonation)
class RecurringDonationAdmin(admin.ModelAdmin):
    list_display = ['subscription_id', 'donor', 'amount', 'frequency', 
                   'status', 'next_payment_date', 'total_payments']
    list_filter = ['status', 'frequency', 'payment_method', 'start_date']
    search_fields = ['subscription_id', 'donor__email', 'donor__first_name', 
                    'donor__last_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Subscription Information', {
            'fields': ['subscription_id', 'donor', 'donation', 'frequency', 
                      'amount', 'status']
        }),
        ('Payment Schedule', {
            'fields': ['start_date', 'next_payment_date', 'end_date', 
                      'total_payments', 'total_amount']
        }),
        ('Payment Method', {
            'fields': ['payment_method', 'payment_method_last4']
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    actions = ['cancel_subscriptions', 'pause_subscriptions']
    
    def cancel_subscriptions(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f"{updated} subscriptions cancelled.")
    cancel_subscriptions.short_description = "Cancel selected subscriptions"
    
    def pause_subscriptions(self, request, queryset):
        updated = queryset.update(status='paused')
        self.message_user(request, f"{updated} subscriptions paused.")
    pause_subscriptions.short_description = "Pause selected subscriptions"


@admin.register(DonationReceipt)
class DonationReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'donation', 'sent_via_email', 
                   'sent_via_sms', 'sent_at']
    list_filter = ['sent_via_email', 'sent_via_sms', 'sent_at']
    search_fields = ['receipt_number', 'donation__donation_id', 
                    'donation__donor_name']
    readonly_fields = ['created_at']


@admin.register(ImpactReport)
class ImpactReportAdmin(admin.ModelAdmin):
    list_display = ['title', 'donation_range_min', 'donation_range_max', 
                   'is_active']
    list_editable = ['is_active']
    list_filter = ['is_active']
    search_fields = ['title', 'description']


# Custom admin dashboard for donations
class DonationAdminDashboard(admin.AdminSite):
    site_header = "Victory Teens Donation Management"
    site_title = "Donation Admin"
    index_title = "Donation Dashboard"

donation_admin = DonationAdminDashboard(name='donation_admin')
donation_admin.register(Donation, DonationAdmin)
donation_admin.register(RecurringDonation, RecurringDonationAdmin)