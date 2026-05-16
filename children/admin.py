from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from datetime import timezone

from .models import (
    ChildCategory, Child, ChildPhoto, ChildStory, 
    Need, Sponsorship, ChildUpdate
)

@admin.register(ChildCategory)
class ChildCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon', 'is_active', 'order']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']



class ChildPhotoInline(admin.TabularInline):
    model = ChildPhoto
    extra = 1
    fields = ['photo', 'photo_type', 'caption', 'is_approved', 'can_display_publicly', 'display_order']
    readonly_fields = ['blur_applied']


class ChildStoryInline(admin.TabularInline):
    model = ChildStory
    extra = 1
    fields = ['title', 'story_type', 'is_approved', 'is_published', 'display_order']


class NeedInline(admin.TabularInline):
    model = Need
    extra = 1
    fields = ['title', 'need_type', 'priority', 'estimated_cost', 'status', 'is_public']


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ['code_name', 'internal_id', 'age', 'gender', 'status', 
                   'is_published', 'is_sponsored', 'date_admitted']
    list_filter = ['status', 'is_published', 'is_sponsored', 'gender', 
                  'categories', 'date_admitted']
    search_fields = ['code_name', 'internal_id', 'background_summary', 
                    'interests', 'private_background']
    readonly_fields = ['internal_id', 'slug', 'current_age', 'years_in_care', 
                      'created_at', 'updated_at']
    list_per_page = 50
    
    fieldsets = [
        ('Identification', {
            'fields': ['code_name', 'internal_id', 'slug', 'categories']
        }),
        ('Basic Information (Public)', {
            'fields': ['gender', 'age', 'background_summary', 'interests', 
                      'educational_level', 'career_aspirations']
        }),
        ('Private Information (Staff Only)', {
            'fields': ['date_of_birth', 'place_of_birth', 'private_background', 
                      'health_status', 'special_needs', 'current_needs'],
            'classes': ['collapse']
        }),
        ('Status & Dates', {
            'fields': ['status', 'date_admitted', 'date_departed', 
                      'case_manager', 'notes']
        }),
        ('Sponsorship', {
            'fields': ['is_sponsored', 'sponsorship_needed', 'sponsorship_amount']
        }),
        ('Privacy & Consent', {
            'fields': ['photo_consent', 'story_consent', 'consent_date', 
                      'consent_expiry']
        }),
        ('Display Settings', {
            'fields': ['is_featured', 'is_published', 'display_order']
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    inlines = [ChildPhotoInline, ChildStoryInline, NeedInline]
    
    actions = ['publish_children', 'unpublish_children', 'mark_as_sponsored']
    
    def publish_children(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f"{updated} children published.")
    publish_children.short_description = "Publish selected children"
    
    def unpublish_children(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f"{updated} children unpublished.")
    unpublish_children.short_description = "Unpublish selected children"
    
    def mark_as_sponsored(self, request, queryset):
        updated = queryset.update(is_sponsored=True)
        self.message_user(request, f"{updated} children marked as sponsored.")
    mark_as_sponsored.short_description = "Mark selected children as sponsored"


@admin.register(ChildPhoto)
class ChildPhotoAdmin(admin.ModelAdmin):
    list_display = ['child', 'photo_type', 'is_approved', 'can_display_publicly', 
                   'requires_blur', 'blur_applied', 'created_at']
    list_filter = ['is_approved', 'can_display_publicly', 'requires_blur', 
                  'blur_applied', 'photo_type', 'created_at']
    search_fields = ['child__code_name', 'caption']
    list_editable = ['is_approved', 'can_display_publicly', 'requires_blur']
    
    fieldsets = [
        ('Photo Information', {
            'fields': ['child', 'photo', 'photo_type', 'caption']
        }),
        ('Privacy Controls', {
            'fields': ['is_approved', 'requires_blur', 'blur_applied', 
                      'can_display_publicly']
        }),
        ('Display Settings', {
            'fields': ['is_featured', 'display_order']
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', obj.photo.url)
        return "-"
    photo_preview.short_description = 'Preview'


@admin.register(ChildStory)
class ChildStoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'child', 'story_type', 'is_approved', 'is_published', 
                   'created_at']
    list_filter = ['is_approved', 'is_published', 'story_type', 'created_at']
    search_fields = ['title', 'content', 'child__code_name']
    list_editable = ['is_approved', 'is_published']
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = [
        ('Story Information', {
            'fields': ['child', 'title', 'slug', 'story_type', 'content', 'excerpt']
        }),
        ('Privacy & Display', {
            'fields': ['is_approved', 'can_display_publicly', 'is_featured', 
                      'is_published', 'display_order']
        }),
        ('Associated Photos', {
            'fields': ['photos'],
            'classes': ['collapse']
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]


@admin.register(Need)
class NeedAdmin(admin.ModelAdmin):
    list_display = ['title', 'child', 'need_type', 'priority', 'estimated_cost', 
                   'amount_raised', 'progress_bar', 'status', 'is_public']
    list_filter = ['status', 'priority', 'need_type', 'is_public', 'created_at']
    search_fields = ['title', 'description', 'child__code_name']
    list_editable = ['priority', 'status', 'is_public']
    
    fieldsets = [
        ('Need Information', {
            'fields': ['child', 'title', 'need_type', 'description', 'priority']
        }),
        ('Funding Information', {
            'fields': ['estimated_cost', 'amount_raised', 'is_fully_funded']
        }),
        ('Timeline', {
            'fields': ['start_date', 'expected_completion', 'completed_date']
        }),
        ('Status & Display', {
            'fields': ['status', 'is_public', 'display_order']
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    readonly_fields = ['is_fully_funded', 'created_at', 'updated_at']
    
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


@admin.register(Sponsorship)
class SponsorshipAdmin(admin.ModelAdmin):
    list_display = ['child', 'sponsor', 'sponsorship_type', 'monthly_amount', 
                   'status', 'start_date', 'is_approved']
    list_filter = ['status', 'sponsorship_type', 'is_approved', 'start_date', 
                  'payment_method']
    search_fields = ['child__code_name', 'sponsor__email', 'sponsor__first_name', 
                    'sponsor__last_name']
    list_editable = ['status', 'is_approved']
    
    fieldsets = [
        ('Sponsorship Details', {
            'fields': ['child', 'sponsor', 'sponsorship_type', 'monthly_amount', 
                      'status', 'is_approved']
        }),
        ('Timeline', {
            'fields': ['start_date', 'end_date']
        }),
        ('Communication', {
            'fields': ['can_receive_updates', 'can_send_messages', 
                      'communication_frequency']
        }),
        ('Payment', {
            'fields': ['is_recurring', 'payment_method', 'last_payment_date', 
                      'next_payment_date']
        }),
        ('Administrative', {
            'fields': ['notes', 'approved_by', 'approved_date'],
            'classes': ['collapse']
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['approve_sponsorships', 'mark_as_active', 'mark_as_cancelled']
    
    def approve_sponsorships(self, request, queryset):
        updated = queryset.update(is_approved=True, approved_by=request.user, 
                                 approved_date=timezone.now())
        self.message_user(request, f"{updated} sponsorships approved.")
    approve_sponsorships.short_description = "Approve selected sponsorships"
    
    def mark_as_active(self, request, queryset):
        updated = queryset.update(status='active')
        self.message_user(request, f"{updated} sponsorships marked as active.")
    mark_as_active.short_description = "Mark selected sponsorships as active"
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f"{updated} sponsorships marked as cancelled.")
    mark_as_cancelled.short_description = "Mark selected sponsorships as cancelled"


@admin.register(ChildUpdate)
class ChildUpdateAdmin(admin.ModelAdmin):
    list_display = ['title', 'child', 'update_type', 'is_approved', 
                   'can_share_publicly', 'sent_to_sponsors', 'created_at']
    list_filter = ['is_approved', 'can_share_publicly', 'sent_to_sponsors', 
                  'update_type', 'created_at']
    search_fields = ['title', 'content', 'child__code_name']
    list_editable = ['is_approved', 'can_share_publicly', 'sent_to_sponsors']
    
    fieldsets = [
        ('Update Information', {
            'fields': ['child', 'title', 'update_type', 'content']
        }),
        ('Privacy & Sharing', {
            'fields': ['is_approved', 'can_share_publicly']
        }),
        ('Delivery', {
            'fields': ['sent_to_sponsors', 'sent_date']
        }),
        ('Associated Photos', {
            'fields': ['photos'],
            'classes': ['collapse']
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    readonly_fields = ['created_at', 'updated_at']
    
    actions = ['approve_updates', 'send_to_sponsors']
    
    def approve_updates(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} updates approved.")
    approve_updates.short_description = "Approve selected updates"
    
    def send_to_sponsors(self, request, queryset):
        # In production, this would send emails to sponsors
        updated = queryset.update(sent_to_sponsors=True, sent_date=timezone.now())
        self.message_user(request, f"{updated} updates marked as sent to sponsors.")
    send_to_sponsors.short_description = "Mark as sent to sponsors"