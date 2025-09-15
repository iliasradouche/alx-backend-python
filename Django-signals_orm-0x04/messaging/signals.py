from django.db.models.signals import post_save, pre_save, post_delete
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
            notification_type="message",
            title=notification_title,
            content=notification_content,
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
        instance.save(update_fields=["is_read"])


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
                last_history = (
                    MessageHistory.objects.filter(message=instance)
                    .order_by("-version")
                    .first()
                )

                next_version = (last_history.version + 1) if last_history else 1

                # Create history entry with old content
                MessageHistory.objects.create(
                    message=instance,
                    old_content=old_message.content,
                    edited_by=getattr(
                        instance, "_edited_by", instance.sender
                    ),  # Use _edited_by if set, fallback to sender
                    version=next_version,
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
        notification_type="system",
        title=title,
        content=content,
    )


def mark_all_notifications_read(user):
    """
    Utility function to mark all notifications as read for a specific user.

    Args:
        user: User instance whose notifications should be marked as read

    Returns:
        int: Number of notifications updated
    """
    return Notification.objects.filter(user=user, is_read=False).update(is_read=True)


def get_unread_notification_count(user):
    """
    Utility function to get the count of unread notifications for a user.

    Args:
        user: User instance

    Returns:
        int: Number of unread notifications
    """
    return Notification.objects.filter(user=user, is_read=False).count()


@receiver(post_delete, sender=User)
def cleanup_user_data(sender, instance, **kwargs):
    """
    Signal handler to clean up all related data when a user is deleted.

    This signal is triggered after a User instance is deleted and handles
    the cleanup of all related messaging data including:
    - Messages sent by the user
    - Messages received by the user
    - Notifications for the user
    - Message histories edited by the user

    Args:
        sender: The User model class
        instance: The User instance that was deleted
        **kwargs: Additional keyword arguments
    """
    try:
        # Note: Due to foreign key relationships with CASCADE delete,
        # most related data should be automatically deleted by Django.
        # However, we can add custom cleanup logic here if needed.

        # Log the cleanup operation
        print(
            f"Cleaning up data for deleted user: {instance.username} (ID: {instance.id})"
        )

        # Custom cleanup for any data that might not be handled by CASCADE
        # For example, if there are any soft-deleted records or special cases

        # Clean up messages sent by or received by this user
        # (This provides explicit cleanup even though CASCADE should handle it)
        sent_messages = Message.objects.filter(sender=instance)
        received_messages = Message.objects.filter(receiver=instance)
        
        sent_count = sent_messages.count()
        received_count = received_messages.count()
        
        sent_messages.delete()
        received_messages.delete()
        
        print(f"Cleaned up {sent_count} sent messages and {received_count} received messages")

        # Clean up any orphaned message histories that might reference this user
        # (This is mainly for safety, as the foreign key should handle this)
        orphaned_histories = MessageHistory.objects.filter(
            edited_by_id=instance.id
        ).exclude(edited_by__isnull=False)

        if orphaned_histories.exists():
            orphaned_count = orphaned_histories.count()
            orphaned_histories.delete()
            print(
                f"Cleaned up {orphaned_count} orphaned message histories for user {instance.username}"
            )

        # Additional cleanup can be added here for other models or special cases
        # For example, clearing user references in logs, analytics, etc.

        print(f"Successfully completed cleanup for user: {instance.username}")

    except Exception as e:
        # Log the error but don't raise it to avoid interfering with the deletion
        print(f"Error during user data cleanup for {instance.username}: {str(e)}")
        # In a production environment, you might want to log this to a proper logging system
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"User data cleanup failed for {instance.username}: {str(e)}")