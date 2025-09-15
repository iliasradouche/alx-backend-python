from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Message, Notification, MessageHistory


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """
    Signal handler that creates a notification when a new message is created.
    
    Args:
        sender: The model class (Message)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        # Only create notification for new messages, not updates
        notification_title = f"New message from {instance.sender.username}"
        notification_content = f"You have received a new message: '{instance.content[:50]}{'...' if len(instance.content) > 50 else ''}'"
        
        # Create notification for the receiver
        Notification.objects.create(
            user=instance.receiver,
            message=instance,
            notification_type='message',
            title=notification_title,
            content=notification_content
        )


@receiver(post_save, sender=Message)
def mark_message_as_unread(sender, instance, created, **kwargs):
    """
    Signal handler that ensures new messages are marked as unread.
    This is a safety measure to ensure proper message state.
    
    Args:
        sender: The model class (Message)
        instance: The actual instance being saved
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created and instance.is_read:
        # Ensure new messages are always unread initially
        instance.is_read = False
        instance.save(update_fields=['is_read'])


@receiver(pre_save, sender=Message)
def log_message_edit_history(sender, instance, **kwargs):
    """
    Signal handler that logs the old content of a message before it's updated.
    This creates a history entry when a message is edited.
    
    Args:
        sender: The model class (Message)
        instance: The actual instance being saved
        **kwargs: Additional keyword arguments
    """
    if instance.pk:  # Only for existing messages (updates, not new creations)
        try:
            # Get the current version from database
            old_message = Message.objects.get(pk=instance.pk)
            
            # Check if content has actually changed
            if old_message.content != instance.content:
                # Get the next version number
                last_history = MessageHistory.objects.filter(
                    message=instance
                ).order_by('-version').first()
                
                next_version = (last_history.version + 1) if last_history else 1
                
                # Create history entry with old content
                MessageHistory.objects.create(
                    message=instance,
                    old_content=old_message.content,
                    edited_by=getattr(instance, '_edited_by', instance.sender),  # Use _edited_by if set, fallback to sender
                    version=next_version
                )
                
                # Mark message as edited
                instance.edited = True
                instance.edited_at = timezone.now()
                
        except Message.DoesNotExist:
            # This shouldn't happen, but handle gracefully
            pass


def create_system_notification(user, title, content):
    """
    Utility function to create system notifications.
    
    Args:
        user: User instance to receive the notification
        title: Notification title
        content: Notification content
    
    Returns:
        Notification: The created notification instance
    """
    return Notification.objects.create(
        user=user,
        message=None,  # System notifications don't have associated messages
        notification_type='system',
        title=title,
        content=content
    )


def mark_all_notifications_read(user):
    """
    Utility function to mark all notifications as read for a specific user.
    
    Args:
        user: User instance whose notifications should be marked as read
    
    Returns:
        int: Number of notifications updated
    """
    return Notification.objects.filter(
        user=user,
        is_read=False
    ).update(is_read=True)


def get_unread_notification_count(user):
    """
    Utility function to get the count of unread notifications for a user.
    
    Args:
        user: User instance
    
    Returns:
        int: Number of unread notifications
    """
    return Notification.objects.filter(
        user=user,
        is_read=False
    ).count()