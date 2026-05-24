from django.contrib import admin
from .models import (
    SiteConfiguration, SiteSettings, ImpactStat, Program, ProgramFeature,
    Testimonial, Teen, FAQ, Page, ContactMessage, Milestone,
    TeamMember, OrganizationProfile, CoreValue
)

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ('id', 'years_of_impact', 'lives_supported', 'partners_count', 'updated_at')
    fieldsets = (
        ('Hero Content', {
            'fields': ('hero_badge', 'hero_title', 'hero_subtitle', 'hero_image')
        }),
        ('Statistics', {
            'fields': ('years_of_impact', 'lives_supported', 'partners_count')
        }),
        ('Call to Action', {
            'fields': ('primary_cta_text', 'primary_cta_url_name', 
                       'secondary_cta_text', 'secondary_cta_url_name')
        }),
    )
    readonly_fields = ('hero_image_preview',)
    
    def hero_image_preview(self, obj):
        if obj.hero_image:
            from django.utils.safestring import mark_safe
            return mark_safe(f'<img src="{obj.hero_image.url}" width="150" />')
        return "No image"
    hero_image_preview.short_description = "Hero Preview"

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'contact_email', 'site_maintenance', 'updated_at')
    fieldsets = (
        ('Basic Info', {'fields': ('site_name', 'tagline', 'contact_email', 'contact_phone', 'address')}),
        ('Social Media', {'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url')}),
        ('Donations', {'fields': ('donation_goal', 'donation_currency', 'show_live_donations', 'show_impact_stats')}),
        ('Maintenance', {'fields': ('site_maintenance', 'maintenance_message')}),
        ('SEO', {'fields': ('meta_description', 'meta_keywords')}),
    )

@admin.register(ImpactStat)
class ImpactStatAdmin(admin.ModelAdmin):
    list_display = ('title', 'value', 'suffix', 'icon', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
   

class ProgramFeatureInline(admin.TabularInline):
    model = ProgramFeature
    extra = 1

# Optionally attach inline to ProgramAdmin
# ProgramAdmin.inlines = [ProgramFeatureInline]

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active', 'order')
    search_fields = ('name', 'content')
    list_per_page = 20

@admin.register(Teen)
class TeenAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'age', 'is_featured', 'joined_date')
    list_filter = ('is_featured', 'age')
    search_fields = ('first_name', 'last_name', 'story')
    list_editable = ('is_featured',)

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer')

@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'show_in_navigation', 'navigation_order')
    list_editable = ('is_published', 'show_in_navigation', 'navigation_order')
    list_filter = ('is_published', 'show_in_navigation')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    list_editable = ('status',)
    readonly_fields = ('ip_address', 'user_agent', 'created_at')

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('year', 'title', 'order')
    list_editable = ('order',)
    search_fields = ('title', 'description')

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'role', 'bio')

@admin.register(OrganizationProfile)
class OrganizationProfileAdmin(admin.ModelAdmin):
    list_display = ('id',)
    fieldsets = (
        ('Mission & Vision', {'fields': ('mission', 'vision', 'image')}),
    )

@admin.register(CoreValue)
class CoreValueAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'order')
    list_editable = ('order',)
    search_fields = ('title', 'description')