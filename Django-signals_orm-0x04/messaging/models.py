from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UnreadMessagesManager(models.Manager):
    """
    Custom manager to filter unread messages for a specific user.
    Optimizes queries with .only() to retrieve only necessary fields.
    """
    
    def for_user(self, user):
        """
        Get all unread messages for a specific user (as receiver).
        Uses .only() to optimize query by retrieving only necessary fields.
        """
        return self.filter(
            receiver=user,
            is_read=False
        ).select_related(
            'sender', 'parent_message'
        ).only(
            'id', 'content', 'timestamp', 'is_read',
            'sender__username', 'sender__first_name', 'sender__last_name',
            'parent_message__id', 'parent_message__content'
        ).order_by('-timestamp')
    
    def unread_count_for_user(self, user):
        """
        Get count of unread messages for a user.
        """
        return self.filter(receiver=user, is_read=False).count()
    
    def mark_as_read_for_user(self, user, message_ids=None):
        """
        Mark messages as read for a user.
        If message_ids is provided, mark only those messages.
        Otherwise, mark all unread messages for the user.
        """
        queryset = self.filter(receiver=user, is_read=False)
        if message_ids:
            queryset = queryset.filter(id__in=message_ids)
        return queryset.update(is_read=True)


class Message(models.Model):
    """
    Model representing a message sent between users with threading support.
    """

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_messages",
        help_text="User who sent the message",
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_messages",
        help_text="User who receives the message",
    )
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name="replies",
        null=True,
        blank=True,
        help_text="Parent message if this is a reply",
    )
    content = models.TextField(help_text="Content of the message")
    timestamp = models.DateTimeField(
        default=timezone.now, help_text="When the message was created"
    )
    is_read = models.BooleanField(
        default=False, help_text="Whether the message has been read by the receiver"
    )
    edited = models.BooleanField(
        default=False, help_text="Whether the message has been edited"
    )
    edited_at = models.DateTimeField(
        null=True, blank=True, help_text="When the message was last edited"
    )

    # Managers
    objects = models.Manager()  # Default manager
    unread = UnreadMessagesManager()  # Custom manager for unread messages

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username} at {self.timestamp}"

    def mark_as_edited(self):
        """Mark this message as edited and update the edited timestamp."""
        self.edited = True
        self.edited_at = timezone.now()
        self.save(update_fields=["edited", "edited_at"])

    @classmethod
    def get_conversations_optimized(cls, user):
        """Get all conversations for a user with optimized queries."""
        return cls.objects.filter(
            models.Q(sender=user) | models.Q(receiver=user)
        ).select_related(
            'sender', 'receiver', 'parent_message'
        ).prefetch_related(
            'replies__sender', 'replies__receiver'
        ).order_by('-timestamp')

    @classmethod
    def get_thread_optimized(cls, root_message_id):
        """Get a complete message thread with optimized queries."""
        return cls.objects.filter(
            models.Q(id=root_message_id) | models.Q(parent_message_id=root_message_id)
        ).select_related(
            'sender', 'receiver', 'parent_message'
        ).prefetch_related(
            'replies__sender', 'replies__receiver'
        ).order_by('timestamp')

    def get_all_replies_recursive(self):
        """Recursively get all replies to this message."""
        def get_replies_tree(message, depth=0):
            replies = []
            direct_replies = message.replies.select_related(
                'sender', 'receiver'
            ).order_by('timestamp')
            
            for reply in direct_replies:
                reply_data = {
                    'message': reply,
                    'depth': depth,
                    'replies': get_replies_tree(reply, depth + 1)
                }
                replies.append(reply_data)
            return replies
        
        return get_replies_tree(self)

    def is_reply(self):
        """Check if this message is a reply to another message."""
        return self.parent_message is not None

    def get_thread_root(self):
        """Get the root message of this thread."""
        if self.parent_message:
            return self.parent_message.get_thread_root()
        return self


class MessageHistory(models.Model):
    """
    Model to store the history of message edits.
    Each time a message is edited, the old content is saved here.
    """

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="history",
        help_text="The message this history entry belongs to",
    )
    old_content = models.TextField(
        help_text="The previous content of the message before edit"
    )
    edited_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="message_edits",
        help_text="User who made the edit",
    )
    edited_at = models.DateTimeField(
        default=timezone.now, help_text="When the edit was made"
    )
    version = models.PositiveIntegerField(
        help_text="Version number of this edit (1 = original, 2 = first edit, etc.)"
    )

    class Meta:
        ordering = ["-edited_at"]
        verbose_name = "Message History"
        verbose_name_plural = "Message Histories"
        unique_together = ["message", "version"]
        indexes = [
            models.Index(fields=["message", "-edited_at"]),
            models.Index(fields=["edited_by", "-edited_at"]),
        ]

    def __str__(self):
        return f"History v{self.version} for message {self.message.id} edited by {self.edited_by.username}"


class Notification(models.Model):
    """
    Model representing a notification for a user about a new message.
    """

    NOTIFICATION_TYPES = [
        ("message", "New Message"),
        ("system", "System Notification"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="User who receives the notification",
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="Message that triggered this notification",
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default="message",
        help_text="Type of notification",
    )
    title = models.CharField(max_length=200, help_text="Notification title")
    content = models.TextField(help_text="Notification content/description")
    is_read = models.BooleanField(
        default=False, help_text="Whether the notification has been read"
    )
    created_at = models.DateTimeField(
        default=timezone.now, help_text="When the notification was created"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["is_read"]),
        ]

    def __str__(self):
        return f"Notification for {self.user.username}: {self.title}"

    def mark_as_read(self):
        """Mark this notification as read."""
        self.is_read = True
        self.save(update_fields=["is_read"])
