from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Message, Notification, MessageHistory


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
        'edited',
        'edited_at',
        'edit_count',
        'notification_count'
    ]
    list_filter = [
        'is_read',
        'edited',
        'timestamp',
        'edited_at',
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
        'edited_at',
        'notification_count',
        'edit_count',
        'edit_history_display'
    ]
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    list_per_page = 25

    fieldsets = (
        ('Message Details', {
            'fields': ('sender', 'receiver', 'content')
        }),
        ('Edit Information', {
            'fields': ('edited', 'edited_at', 'edit_count', 'edit_history_display'),
            'classes': ('collapse',)
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

    def edit_count(self, obj):
        """
        Display the number of times this message has been edited.
        """
        count = obj.messagehistory_set.count()
        if count > 0:
            return format_html(
                '<span style="color: orange; font-weight: bold;">{} edit{}</span>',
                count,
                's' if count != 1 else ''
            )
        return format_html('<span style="color: green;">No edits</span>')
    
    edit_count.short_description = 'Edit Count'

    def edit_history_display(self, obj):
        """
        Display the edit history of the message in a formatted way.
        """
        history_entries = obj.messagehistory_set.all().order_by('-version')
        
        if not history_entries.exists():
            return format_html('<em>No edit history</em>')
        
        html_parts = ['<div style="max-height: 300px; overflow-y: auto;">']
        html_parts.append('<table style="width: 100%; border-collapse: collapse;">')
        html_parts.append(
            '<tr style="background-color: #f0f0f0; font-weight: bold;">' +
            '<th style="padding: 5px; border: 1px solid #ddd;">Version</th>' +
            '<th style="padding: 5px; border: 1px solid #ddd;">Edited By</th>' +
            '<th style="padding: 5px; border: 1px solid #ddd;">Date</th>' +
            '<th style="padding: 5px; border: 1px solid #ddd;">Previous Content</th>' +
            '</tr>'
        )
        
        for entry in history_entries:
            content_preview = entry.old_content[:100] + '...' if len(entry.old_content) > 100 else entry.old_content
            html_parts.append(
                f'<tr>' +
                f'<td style="padding: 5px; border: 1px solid #ddd; text-align: center;">{entry.version}</td>' +
                f'<td style="padding: 5px; border: 1px solid #ddd;">{entry.edited_by.username}</td>' +
                f'<td style="padding: 5px; border: 1px solid #ddd;">{entry.edited_at.strftime("%Y-%m-%d %H:%M")}</td>' +
                f'<td style="padding: 5px; border: 1px solid #ddd;">{content_preview}</td>' +
                f'</tr>'
            )
        
        html_parts.append('</table>')
        html_parts.append('</div>')
        
        return format_html(''.join(html_parts))
    
    edit_history_display.short_description = 'Edit History'

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


@admin.register(MessageHistory)
class MessageHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for MessageHistory model.
    """
    list_display = [
        'id',
        'message_link',
        'version',
        'edited_by_link',
        'edited_at',
        'old_content_preview'
    ]
    list_filter = [
        'edited_at',
        'version',
        'edited_by',
        'message__sender'
    ]
    search_fields = [
        'message__content',
        'old_content',
        'edited_by__username',
        'message__sender__username',
        'message__receiver__username'
    ]
    readonly_fields = [
        'message',
        'old_content',
        'edited_by',
        'edited_at',
        'version',
        'message_details'
    ]
    date_hierarchy = 'edited_at'
    ordering = ['-edited_at']
    list_per_page = 25

    fieldsets = (
        ('History Entry Details', {
            'fields': ('message', 'version', 'old_content')
        }),
        ('Edit Information', {
            'fields': ('edited_by', 'edited_at')
        }),
        ('Related Message Info', {
            'fields': ('message_details',),
            'classes': ('collapse',)
        })
    )

    def message_link(self, obj):
        """Create a link to the related message in admin."""
        url = reverse('admin:messaging_message_change', args=[obj.message.pk])
        return format_html('<a href="{}">{}</a>', url, f'Message #{obj.message.pk}')
    
    message_link.short_description = 'Message'
    message_link.admin_order_field = 'message'

    def edited_by_link(self, obj):
        """Create a link to the user who edited the message."""
        url = reverse('admin:auth_user_change', args=[obj.edited_by.pk])
        return format_html('<a href="{}">{}</a>', url, obj.edited_by.username)
    
    edited_by_link.short_description = 'Edited By'
    edited_by_link.admin_order_field = 'edited_by__username'

    def old_content_preview(self, obj):
        """Show a preview of the old content."""
        preview = obj.old_content[:100] + '...' if len(obj.old_content) > 100 else obj.old_content
        return format_html('<span title="{}">{}</span>', obj.old_content, preview)
    
    old_content_preview.short_description = 'Old Content Preview'

    def message_details(self, obj):
        """Display detailed information about the related message."""
        message = obj.message
        return format_html(
            '<div>' +
            '<strong>Current Content:</strong> {}<br>' +
            '<strong>Sender:</strong> {}<br>' +
            '<strong>Receiver:</strong> {}<br>' +
            '<strong>Created:</strong> {}<br>' +
            '<strong>Is Read:</strong> {}' +
            '</div>',
            message.content[:200] + '...' if len(message.content) > 200 else message.content,
            message.sender.username,
            message.receiver.username,
            message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'Yes' if message.is_read else 'No'
        )
    
    message_details.short_description = 'Message Details'

    def get_queryset(self, request):
        """Optimize queryset with select_related for better performance."""
        return super().get_queryset(request).select_related(
            'message', 'edited_by', 'message__sender', 'message__receiver'
        )

    def has_add_permission(self, request):
        """Disable adding MessageHistory entries manually."""
        return False

    def has_change_permission(self, request, obj=None):
        """Disable editing MessageHistory entries."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion of MessageHistory entries."""
        return True