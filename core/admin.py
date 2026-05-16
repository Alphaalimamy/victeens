from django.contrib import admin
from django.utils.html import format_html
from .models import (SiteSettings, ImpactStat, Testimonial,Milestone, FAQ, Page, ProgramFeature,
                     ContactMessage, Program, TeamMember, OrganizationProfile, CoreValue)

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['site_name', 'contact_email', 'updated_at']
    fieldsets = [
        ('Basic Information', {
            'fields': ['site_name', 'tagline', 'contact_email', 'contact_phone', 'address']
        }),
        ('Social Media', {
            'fields': ['facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url']
        }),
        ('Donation Settings', {
            'fields': ['donation_goal', 'donation_currency']
        }),
        ('Transparency Settings', {
            'fields': ['show_live_donations', 'show_impact_stats']
        }),
        ('Maintenance', {
            'fields': ['site_maintenance', 'maintenance_message']
        }),
        ('SEO', {
            'fields': ['meta_description', 'meta_keywords']
        }),
    ]
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not SiteSettings.objects.exists()

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ['title']
    list_filter = ['title']
    search_fields = ['title', 'description']
    

class ProgramFeatureInline(admin.TabularInline):
    model = ProgramFeature
    extra = 1


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_active']
    list_editable = ['is_active']
    list_filter = ['is_active']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProgramFeatureInline]
    
@admin.register(ImpactStat)
class ImpactStatAdmin(admin.ModelAdmin):
    list_display = ['title', 'value', 'suffix', 'is_active', 'order']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['title', 'description']



@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'role', 'is_featured', 'is_approved', 'created_at']
    list_editable = ['is_featured', 'is_approved']
    list_filter = ['is_featured', 'is_approved', 'created_at']
    search_fields = ['name', 'role', 'content']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "-"
    image_preview.short_description = 'Image'






@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_published', 'show_in_navigation', 'created_at']
    list_editable = ['is_published', 'show_in_navigation']
    list_filter = ['is_published', 'show_in_navigation']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['created_at', 'updated_at', 'ip_address', 'user_agent']
    
    fieldsets = [
        ('Message Details', {
            'fields': ['name', 'email', 'phone', 'subject', 'message', 'status']
        }),
        ('Technical Information', {
            'fields': ['ip_address', 'user_agent', 'created_at', 'updated_at'],
            'classes': ['collapse']
        }),
    ]
    
    actions = ['mark_as_read', 'mark_as_replied']
    
    def mark_as_read(self, request, queryset):
        queryset.update(status='read')
        self.message_user(request, f"{queryset.count()} messages marked as read.")
    mark_as_read.short_description = "Mark selected messages as read"
    
    def mark_as_replied(self, request, queryset):
        queryset.update(status='replied')
        self.message_user(request, f"{queryset.count()} messages marked as replied.")
    mark_as_replied.short_description = "Mark selected messages as replied"
    
    

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "order", "is_active")
    list_editable = ("order", "is_active")


@admin.register(CoreValue)
class CoreValueAdmin(admin.ModelAdmin):
    list_display = ("title", "order")
    list_editable = ("order",)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "order", "is_active")
    list_filter = ("category",)
    list_editable = ("order", "is_active")


admin.site.register(OrganizationProfile)
