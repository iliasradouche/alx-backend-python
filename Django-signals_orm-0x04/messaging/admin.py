from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Message, Notification


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """
    Admin interface for Message model.
    """
    list_display = [
        'id',
        'sender_link',
        'receiver_link', 
        'content_preview',
        'timestamp',
        'is_read',
        'notification_count'
    ]
    list_filter = [
        'is_read',
        'timestamp',
        'sender',
        'receiver'
    ]
    search_fields = [
        'sender__username',
        'receiver__username',
        'content'
    ]
    readonly_fields = [
        'timestamp',
        'notification_count'
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    list_per_page = 25

    fieldsets = (
        ('Message Details', {
            'fields': ('sender', 'receiver', 'content')
        }),
        ('Status & Metadata', {
            'fields': ('is_read', 'timestamp', 'notification_count'),
            'classes': ('collapse',)
        })
    )

    def sender_link(self, obj):
        """Create a link to the sender's user admin page."""
        url = reverse('admin:auth_user_change', args=[obj.sender.pk])
        return format_html('<a href="{}">{}</a>', url, obj.sender.username)
    sender_link.short_description = 'Sender'
    sender_link.admin_order_field = 'sender__username'

    def receiver_link(self, obj):
        """Create a link to the receiver's user admin page."""
        url = reverse('admin:auth_user_change', args=[obj.receiver.pk])
        return format_html('<a href="{}">{}</a>', url, obj.receiver.username)
    receiver_link.short_description = 'Receiver'
    receiver_link.admin_order_field = 'receiver__username'

    def content_preview(self, obj):
        """Show a truncated preview of the message content."""
        if len(obj.content) > 50:
            return f"{obj.content[:50]}..."
        return obj.content
    content_preview.short_description = 'Content Preview'

    def notification_count(self, obj):
        """Show the number of notifications created for this message."""
        count = obj.notifications.count()
        if count > 0:
            return format_html(
                '<span style="color: green;">{} notification{}</span>',
                count,
                's' if count != 1 else ''
            )
        return format_html('<span style="color: red;">No notifications</span>')
    notification_count.short_description = 'Notifications'

    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance."""
        return super().get_queryset(request).select_related('sender', 'receiver')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin interface for Notification model.
    """
    list_display = [
        'id',
        'user_link',
        'notification_type',
        'title_preview',
        'message_link',
        'is_read',
        'created_at'
    ]
    list_filter = [
        'is_read',
        'notification_type',
        'created_at',
        'user'
    ]
    search_fields = [
        'user__username',
        'title',
        'content',
        'message__content'
    ]
    readonly_fields = [
        'created_at',
        'message_details'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 25

    fieldsets = (
        ('Notification Details', {
            'fields': ('user', 'notification_type', 'title', 'content')
        }),
        ('Related Message', {
            'fields': ('message', 'message_details'),
            'classes': ('collapse',)
        }),
        ('Status & Metadata', {
            'fields': ('is_read', 'created_at'),
            'classes': ('collapse',)
        })
    )

    actions = ['mark_as_read', 'mark_as_unread']

    def user_link(self, obj):
        """Create a link to the user's admin page."""
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'

    def title_preview(self, obj):
        """Show a truncated preview of the notification title."""
        if len(obj.title) > 30:
            return f"{obj.title[:30]}..."
        return obj.title
    title_preview.short_description = 'Title'

    def message_link(self, obj):
        """Create a link to the related message if it exists."""
        if obj.message:
            url = reverse('admin:messaging_message_change', args=[obj.message.pk])
            return format_html('<a href="{}">Message #{}</a>', url, obj.message.pk)
        return format_html('<span style="color: gray;">No message</span>')
    message_link.short_description = 'Related Message'

    def message_details(self, obj):
        """Show details of the related message."""
        if obj.message:
            return format_html(
                '<strong>From:</strong> {}<br>'
                '<strong>To:</strong> {}<br>'
                '<strong>Content:</strong> {}<br>'
                '<strong>Sent:</strong> {}',
                obj.message.sender.username,
                obj.message.receiver.username,
                obj.message.content[:100] + ('...' if len(obj.message.content) > 100 else ''),
                obj.message.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            )
        return "No related message"
    message_details.short_description = 'Message Details'

    def mark_as_read(self, request, queryset):
        """Admin action to mark selected notifications as read."""
        updated = queryset.update(is_read=True)
        self.message_user(
            request,
            f"{updated} notification{'s' if updated != 1 else ''} marked as read."
        )
    mark_as_read.short_description = "Mark selected notifications as read"

    def mark_as_unread(self, request, queryset):
        """Admin action to mark selected notifications as unread."""
        updated = queryset.update(is_read=False)
        self.message_user(
            request,
            f"{updated} notification{'s' if updated != 1 else ''} marked as unread."
        )
    mark_as_unread.short_description = "Mark selected notifications as unread"

    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance."""
        return super().get_queryset(request).select_related('user', 'message', 'message__sender', 'message__receiver')