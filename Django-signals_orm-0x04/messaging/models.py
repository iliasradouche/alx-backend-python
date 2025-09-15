from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Message(models.Model):
    """
    Model representing a message sent between users.
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
