from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import (
    OrganizationProfiles, SiteConfiguration, SiteSettings, ImpactStat, Program, ProgramFeature,
    Testimonial, Teen, FAQ, Page, ContactMessage, Milestone,
    TeamMember, CoreValue, FocusArea, Impact,
    Partner, NewsletterSubscriber, Donation
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
            return mark_safe(f'<img src="{obj.hero_image.url}" width="150" />')
        return "No image"
    hero_image_preview.short_description = "Hero Preview"
    
    def has_add_permission(self, request):
        # Prevent adding multiple instances
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'contact_email', 'site_maintenance', 'updated_at')
    fieldsets = (
        ('Basic Info', {
            'fields': ('site_name', 'tagline', 'contact_email', 'contact_phone', 'address')
        }),
        ('Social Media', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url'),
            'classes': ('wide',)
        }),
        ('Donations', {
            'fields': ('donation_goal', 'donation_currency', 'show_live_donations', 'show_impact_stats')
        }),
        ('Maintenance', {
            'fields': ('site_maintenance', 'maintenance_message'),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(ImpactStat)
class ImpactStatAdmin(admin.ModelAdmin):
    list_display = ('title', 'value', 'suffix', 'icon', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    list_per_page = 20


class ProgramFeatureInline(admin.TabularInline):
    model = ProgramFeature
    extra = 1
    classes = ('collapse',)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ProgramFeatureInline]
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'description', 'image')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active'),
            'classes': ('wide',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" />')
        return "No image"
    image_preview.short_description = "Preview"
    readonly_fields = ('image_preview',)


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'order', 'is_active', 'created_at')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'content')
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('name', 'role', 'content', 'image')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active'),
            'classes': ('wide',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" style="border-radius: 50%;" />')
        return "No image"
    image_preview.short_description = "Photo"
    readonly_fields = ('image_preview',)


@admin.register(Teen)
class TeenAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'age', 'is_featured', 'joined_date')
    list_filter = ('is_featured', 'age', 'joined_date')
    search_fields = ('first_name', 'last_name', 'story')
    list_editable = ('is_featured',)
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'age', 'photo', 'story')
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'joined_date'),
            'classes': ('wide',)
        }),
    )
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = "Name"
    full_name.admin_order_field = 'first_name'
    
    def photo_preview(self, obj):
        if obj.photo:
            return mark_safe(f'<img src="{obj.photo.url}" width="50" height="50" style="border-radius: 50%;" />')
        return "No photo"
    photo_preview.short_description = "Photo"
    readonly_fields = ('photo_preview',)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('question', 'answer')
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('question', 'answer', 'category')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active'),
            'classes': ('wide',)
        }),
    )


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'show_in_navigation', 'navigation_order')
    list_editable = ('is_published', 'show_in_navigation', 'navigation_order')
    list_filter = ('is_published', 'show_in_navigation', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'content')
        }),
        ('Meta Information', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Navigation Settings', {
            'fields': ('show_in_navigation', 'navigation_order'),
            'classes': ('wide',)
        }),
        ('Publication Settings', {
            'fields': ('is_published',),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        if not obj.meta_title:
            obj.meta_title = obj.title
        super().save_model(request, obj, form, change)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    list_editable = ('status',)
    readonly_fields = ('ip_address', 'user_agent', 'created_at', 'updated_at')
    list_per_page = 20
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Message', {
            'fields': ('subject', 'message')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Technical Information', {
            'fields': ('ip_address', 'user_agent', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_replied']
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(status='read')
        self.message_user(request, f'{updated} messages marked as read.')
    mark_as_read.short_description = "Mark selected messages as read"
    
    def mark_as_replied(self, request, queryset):
        updated = queryset.update(status='replied')
        self.message_user(request, f'{updated} messages marked as replied.')
    mark_as_replied.short_description = "Mark selected messages as replied"


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('year', 'title', 'order', 'highlight_stats')
    list_editable = ('order',)
    search_fields = ('title', 'description')
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('year', 'title', 'description', 'highlight_stats')
        }),
        ('Display Settings', {
            'fields': ('order',),
            'classes': ('wide',)
        }),
    )


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('name','bio')
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('name', 'role','bio', 'image')
        }),
        ('Contact Information', {
            'fields': ('email', 'linkedin_url'),
            'classes': ('wide',)
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active'),
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" style="border-radius: 50%;" />')
        return "No image"
    image_preview.short_description = "Photo"
    readonly_fields = ('image_preview',)


@admin.register(OrganizationProfiles)
class OrganizationProfileAdmin(admin.ModelAdmin):
    list_display = ('id',)
    fieldsets = (
        ('Organization History', { 
            'fields': ('history',),
        }),
        ('Mission & Vision', {
            'fields': ('mission', 'vision', 'image', 'background_image')
        }),
    )
    
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(CoreValue)
class CoreValueAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'description')
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('title', 'icon', 'description')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active'),
        }),
    )
    
    def icon_preview(self, obj):
        return mark_safe(f'<i class="{obj.icon}" style="font-size: 24px;"></i>')
    icon_preview.short_description = "Icon Preview"


@admin.register(FocusArea)
class FocusAreaAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'description')
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('title', 'icon', 'description')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active'),
        }),
    )


@admin.register(Impact)
class ImpactAdmin(admin.ModelAdmin):
    list_display = ('title', 'value', 'icon', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'description')
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('title', 'value', 'icon', 'description')
        }),
        ('Display Settings', {
            'fields': ('order', 'is_active'),
        }),
    )


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'partner_type', 'featured', 'order', 'is_active')
    list_editable = ('order', 'is_active', 'featured')
    list_filter = ('partner_type', 'is_active', 'featured')
    search_fields = ('name', 'description')
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('name', 'partner_type', 'logo', 'website_url', 'description')
        }),
        ('Display Settings', {
            'fields': ('featured', 'order', 'is_active'),
        }),
    )
    
    def logo_preview(self, obj):
        if obj.logo:
            return mark_safe(f'<img src="{obj.logo.url}" width="80" />')
        return "No logo"
    logo_preview.short_description = "Logo"
    readonly_fields = ('logo_preview',)


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'is_active', 'subscribed_at')
    list_filter = ('is_active', 'subscribed_at')
    search_fields = ('email', 'name')
    readonly_fields = ('subscribed_at', 'unsubscribed_at')
    list_per_page = 20
    fieldsets = (
        (None, {
            'fields': ('email', 'name', 'is_active')
        }),
        ('Dates', {
            'fields': ('subscribed_at', 'unsubscribed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_subscribers', 'deactivate_subscribers']
    
    def activate_subscribers(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} subscribers activated.')
    activate_subscribers.short_description = "Activate selected subscribers"
    
    def deactivate_subscribers(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} subscribers deactivated.')
    deactivate_subscribers.short_description = "Deactivate selected subscribers"


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('donor_name', 'donor_email', 'transaction_id')
    readonly_fields = ('created_at',)
    list_per_page = 20
    fieldsets = (
        ('Donor Information', {
            'fields': ('donor_name', 'donor_email', 'donor_phone', 'is_anonymous')
        }),
        ('Donation Details', {
            'fields': ('amount', 'currency', 'message', 'status', 'transaction_id')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    def display_name(self, obj):
        return obj.display_name
    display_name.short_description = "Donor Name"
    display_name.admin_order_field = 'donor_name'
    
    actions = ['mark_as_completed', 'mark_as_refunded']
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} donations marked as completed.')
    mark_as_completed.short_description = "Mark selected as completed"
    
    def mark_as_refunded(self, request, queryset):
        updated = queryset.update(status='refunded')
        self.message_user(request, f'{updated} donations marked as refunded.')
    mark_as_refunded.short_description = "Mark selected as refunded"


# Custom Admin Site Configuration (Optional)
class CustomAdminSite(admin.AdminSite):
    site_header = "Victory Teens Organization Admin"
    site_title = "Victory Teens Admin Portal"
    index_title = "Welcome to Victory Teens Administration"
    
    def get_app_list(self, request):
        """
        Customize the order of apps in the admin dashboard
        """
        app_list = super().get_app_list(request)
        
        # Custom ordering logic here if needed
        return app_list

