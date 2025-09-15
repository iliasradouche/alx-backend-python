from django.test import TestCase
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from unittest.mock import patch
from .models import Message, Notification, MessageHistory
from .signals import (
    create_message_notification,
    mark_message_as_unread,
    log_message_edit_history,
    create_system_notification,
    mark_all_notifications_read,
    get_unread_notification_count
)


class MessageModelTest(TestCase):
    """
    Test cases for the Message model.
    """

    def setUp(self):
        """Set up test data."""
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@test.com',
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver',
            email='receiver@test.com',
            password='testpass123'
        )

    def test_message_creation(self):
        """Test that a message can be created successfully."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Hello, this is a test message!"
        )
        
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.receiver, self.receiver)
        self.assertEqual(message.content, "Hello, this is a test message!")
        self.assertFalse(message.is_read)
        self.assertIsNotNone(message.timestamp)

    def test_message_str_representation(self):
        """Test the string representation of a message."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Test message"
        )
        
        expected_str = f"Message from {self.sender.username} to {self.receiver.username} at {message.timestamp}"
        self.assertEqual(str(message), expected_str)

    def test_message_ordering(self):
        """Test that messages are ordered by timestamp (newest first)."""
        message1 = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="First message"
        )
        message2 = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Second message"
        )
        
        messages = Message.objects.all()
        self.assertEqual(messages[0], message2)  # Newest first
        self.assertEqual(messages[1], message1)


class NotificationModelTest(TestCase):
    """
    Test cases for the Notification model.
    """

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@test.com',
            password='testpass123'
        )
        self.message = Message.objects.create(
            sender=self.sender,
            receiver=self.user,
            content="Test message for notification"
        )

    def test_notification_creation(self):
        """Test that a notification can be created successfully."""
        notification = Notification.objects.create(
            user=self.user,
            message=self.message,
            title="New Message",
            content="You have a new message"
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.message, self.message)
        self.assertEqual(notification.title, "New Message")
        self.assertEqual(notification.content, "You have a new message")
        self.assertEqual(notification.notification_type, 'message')
        self.assertFalse(notification.is_read)


class MessageHistoryModelTest(TestCase):
    """
    Test cases for the MessageHistory model.
    """

    def setUp(self):
        """Set up test data."""
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@test.com',
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver',
            email='receiver@test.com',
            password='testpass123'
        )
        self.editor = User.objects.create_user(
            username='editor',
            email='editor@test.com',
            password='testpass123'
        )
        self.message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original message content"
        )

    def test_message_history_creation(self):
        """Test that a MessageHistory entry can be created successfully."""
        history = MessageHistory.objects.create(
            message=self.message,
            old_content="Previous content",
            edited_by=self.editor,
            version=1
        )
        
        self.assertEqual(history.message, self.message)
        self.assertEqual(history.old_content, "Previous content")
        self.assertEqual(history.edited_by, self.editor)
        self.assertEqual(history.version, 1)
        self.assertIsNotNone(history.edited_at)

    def test_message_history_str_representation(self):
        """Test the string representation of a MessageHistory entry."""
        history = MessageHistory.objects.create(
            message=self.message,
            old_content="Previous content",
            edited_by=self.editor,
            version=1
        )
        
        expected_str = f"Message #{self.message.pk} - Version 1 (edited by {self.editor.username})"
        self.assertEqual(str(history), expected_str)

    def test_message_history_ordering(self):
        """Test that MessageHistory entries are ordered by edited_at descending."""
        # Create multiple history entries
        history1 = MessageHistory.objects.create(
            message=self.message,
            old_content="First edit",
            edited_by=self.editor,
            version=1
        )
        history2 = MessageHistory.objects.create(
            message=self.message,
            old_content="Second edit",
            edited_by=self.editor,
            version=2
        )
        
        # Get all history entries
        histories = list(MessageHistory.objects.all())
        
        # Should be ordered by edited_at descending (newest first)
        self.assertEqual(histories[0], history2)
        self.assertEqual(histories[1], history1)

    def test_message_history_unique_together(self):
        """Test that message and version combination must be unique."""
        MessageHistory.objects.create(
            message=self.message,
            old_content="First version",
            edited_by=self.editor,
            version=1
        )
        
        # Attempting to create another history entry with same message and version should fail
        with self.assertRaises(Exception):  # IntegrityError in real database
            MessageHistory.objects.create(
                message=self.message,
                old_content="Duplicate version",
                edited_by=self.editor,
                version=1
            )


class MessageEditingTest(TestCase):
    """
    Test cases for message editing functionality.
    """

    def setUp(self):
        """Set up test data."""
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@test.com',
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver',
            email='receiver@test.com',
            password='testpass123'
        )
        self.editor = User.objects.create_user(
            username='editor',
            email='editor@test.com',
            password='testpass123'
        )

    def test_message_edited_field_default(self):
        """Test that new messages have edited=False by default."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original content"
        )
        
        self.assertFalse(message.edited)
        self.assertIsNone(message.edited_at)

    def test_mark_as_edited_method(self):
        """Test the mark_as_edited method."""
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original content"
        )
        
        # Mark as edited
        message.mark_as_edited()
        
        self.assertTrue(message.edited)
        self.assertIsNotNone(message.edited_at)

    def test_pre_save_signal_creates_history(self):
        """Test that the pre_save signal creates history when content changes."""
        # Create initial message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original content"
        )
        
        # Verify no history exists initially
        self.assertEqual(MessageHistory.objects.count(), 0)
        
        # Edit the message content
        message._edited_by = self.editor  # Set the editor
        message.content = "Updated content"
        message.save()
        
        # Verify history was created
        self.assertEqual(MessageHistory.objects.count(), 1)
        
        history = MessageHistory.objects.first()
        self.assertEqual(history.message, message)
        self.assertEqual(history.old_content, "Original content")
        self.assertEqual(history.edited_by, self.editor)
        self.assertEqual(history.version, 1)
        
        # Verify message was marked as edited
        message.refresh_from_db()
        self.assertTrue(message.edited)
        self.assertIsNotNone(message.edited_at)

    def test_pre_save_signal_no_history_for_same_content(self):
        """Test that no history is created when content doesn't change."""
        # Create initial message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original content"
        )
        
        # Save again without changing content
        message.save()
        
        # Verify no history was created
        self.assertEqual(MessageHistory.objects.count(), 0)
        self.assertFalse(message.edited)

    def test_pre_save_signal_no_history_for_new_messages(self):
        """Test that no history is created for new messages."""
        # Create new message (this triggers save)
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="New message content"
        )
        
        # Verify no history was created for new message
        self.assertEqual(MessageHistory.objects.count(), 0)
        self.assertFalse(message.edited)

    def test_multiple_edits_create_multiple_history_entries(self):
        """Test that multiple edits create multiple history entries with correct versions."""
        # Create initial message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original content"
        )
        
        # First edit
        message._edited_by = self.editor
        message.content = "First edit"
        message.save()
        
        # Second edit
        message._edited_by = self.sender
        message.content = "Second edit"
        message.save()
        
        # Third edit
        message._edited_by = self.receiver
        message.content = "Third edit"
        message.save()
        
        # Verify three history entries were created
        self.assertEqual(MessageHistory.objects.count(), 3)
        
        # Verify versions are correct
        histories = MessageHistory.objects.order_by('version')
        self.assertEqual(histories[0].version, 1)
        self.assertEqual(histories[0].old_content, "Original content")
        self.assertEqual(histories[0].edited_by, self.editor)
        
        self.assertEqual(histories[1].version, 2)
        self.assertEqual(histories[1].old_content, "First edit")
        self.assertEqual(histories[1].edited_by, self.sender)
        
        self.assertEqual(histories[2].version, 3)
        self.assertEqual(histories[2].old_content, "Second edit")
        self.assertEqual(histories[2].edited_by, self.receiver)

    def test_pre_save_signal_fallback_to_sender(self):
        """Test that the signal falls back to sender when _edited_by is not set."""
        # Create initial message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original content"
        )
        
        # Edit without setting _edited_by
        message.content = "Updated content"
        message.save()
        
        # Verify history was created with sender as editor
        history = MessageHistory.objects.first()
        self.assertEqual(history.edited_by, self.sender)


class MessageEditingIntegrationTest(TestCase):
    """
    Integration tests for the complete message editing workflow.
    """

    def setUp(self):
        """Set up test data."""
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@test.com',
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver',
            email='receiver@test.com',
            password='testpass123'
        )
        self.editor = User.objects.create_user(
            username='editor',
            email='editor@test.com',
            password='testpass123'
        )

    def test_complete_message_editing_workflow(self):
        """Test the complete workflow of creating, editing, and tracking message history."""
        # Step 1: Create initial message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Hello, this is the original message!"
        )
        
        # Verify initial state
        self.assertFalse(message.edited)
        self.assertIsNone(message.edited_at)
        self.assertEqual(MessageHistory.objects.count(), 0)
        
        # Step 2: First edit
        message._edited_by = self.editor
        message.content = "Hello, this message has been edited once!"
        message.save()
        
        # Verify first edit
        message.refresh_from_db()
        self.assertTrue(message.edited)
        self.assertIsNotNone(message.edited_at)
        self.assertEqual(MessageHistory.objects.count(), 1)
        
        first_history = MessageHistory.objects.get(version=1)
        self.assertEqual(first_history.old_content, "Hello, this is the original message!")
        self.assertEqual(first_history.edited_by, self.editor)
        
        # Step 3: Second edit
        message._edited_by = self.sender
        message.content = "Hello, this message has been edited twice!"
        message.save()
        
        # Verify second edit
        self.assertEqual(MessageHistory.objects.count(), 2)
        
        second_history = MessageHistory.objects.get(version=2)
        self.assertEqual(second_history.old_content, "Hello, this message has been edited once!")
        self.assertEqual(second_history.edited_by, self.sender)
        
        # Step 4: Verify current message content
        self.assertEqual(message.content, "Hello, this message has been edited twice!")
        
        # Step 5: Verify history ordering
        histories = MessageHistory.objects.order_by('-version')
        self.assertEqual(list(histories), [second_history, first_history])

    def test_message_with_notifications_and_edits(self):
        """Test that message editing works correctly with the notification system."""
        # Create initial message (this should create a notification)
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original message with notification"
        )
        
        # Verify notification was created
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.first()
        self.assertEqual(notification.message, message)
        
        # Edit the message
        message._edited_by = self.editor
        message.content = "Edited message content"
        message.save()
        
        # Verify notification still exists and points to the same message
        self.assertEqual(Notification.objects.count(), 1)
        notification.refresh_from_db()
        self.assertEqual(notification.message, message)
        
        # Verify history was created
        self.assertEqual(MessageHistory.objects.count(), 1)
        history = MessageHistory.objects.first()
        self.assertEqual(history.old_content, "Original message with notification")
        
        # Verify message is marked as edited
        message.refresh_from_db()
        self.assertTrue(message.edited)

    @patch('messaging.signals.timezone.now')
    def test_edited_at_timestamp_accuracy(self, mock_now):
        """Test that edited_at timestamp is set correctly."""
        from django.utils import timezone as django_timezone
        
        # Mock the current time
        mock_time = django_timezone.datetime(2023, 1, 15, 12, 30, 45, tzinfo=django_timezone.utc)
        mock_now.return_value = mock_time
        
        # Create and edit message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original content"
        )
        
        message._edited_by = self.editor
        message.content = "Edited content"
        message.save()
        
        # Verify edited_at timestamp
        message.refresh_from_db()
        self.assertEqual(message.edited_at, mock_time)
        
        # Verify history timestamp
        history = MessageHistory.objects.first()
        self.assertIsNotNone(history.edited_at)
        self.assertIsNotNone(notification.created_at)

    def test_notification_str_representation(self):
        """Test the string representation of a notification."""
        notification = Notification.objects.create(
            user=self.user,
            message=self.message,
            title="Test Notification",
            content="Test content"
        )
        
        expected_str = f"Notification for {self.user.username}: Test Notification"
        self.assertEqual(str(notification), expected_str)

    def test_mark_as_read_method(self):
        """Test the mark_as_read method."""
        notification = Notification.objects.create(
            user=self.user,
            message=self.message,
            title="Test Notification",
            content="Test content"
        )
        
        self.assertFalse(notification.is_read)
        notification.mark_as_read()
        self.assertTrue(notification.is_read)


class MessageSignalTest(TestCase):
    """
    Test cases for message-related signals.
    """

    def setUp(self):
        """Set up test data."""
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@test.com',
            password='testpass123'
        )
        self.receiver = User.objects.create_user(
            username='receiver',
            email='receiver@test.com',
            password='testpass123'
        )

    def test_notification_created_on_message_creation(self):
        """Test that a notification is automatically created when a message is created."""
        # Ensure no notifications exist initially
        self.assertEqual(Notification.objects.count(), 0)
        
        # Create a message
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Hello, this should trigger a notification!"
        )
        
        # Check that a notification was created
        self.assertEqual(Notification.objects.count(), 1)
        
        notification = Notification.objects.first()
        self.assertEqual(notification.user, self.receiver)
        self.assertEqual(notification.message, message)
        self.assertEqual(notification.notification_type, 'message')
        self.assertIn(self.sender.username, notification.title)
        self.assertIn(message.content[:50], notification.content)

    def test_no_notification_on_message_update(self):
        """Test that no additional notification is created when a message is updated."""
        # Create a message (this will create one notification)
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content="Original content"
        )
        
        self.assertEqual(Notification.objects.count(), 1)
        
        # Update the message
        message.content = "Updated content"
        message.save()
        
        # Should still have only one notification
        self.assertEqual(Notification.objects.count(), 1)

    def test_long_message_content_truncation(self):
        """Test that long message content is properly truncated in notifications."""
        long_content = "This is a very long message content that should be truncated in the notification to avoid overly long notification text."
        
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.receiver,
            content=long_content
        )
        
        notification = Notification.objects.first()
        self.assertIn(long_content[:50], notification.content)
        self.assertIn('...', notification.content)


class SignalUtilityFunctionTest(TestCase):
    """
    Test cases for utility functions in signals.py.
    """

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.sender = User.objects.create_user(
            username='sender',
            email='sender@test.com',
            password='testpass123'
        )

    def test_create_system_notification(self):
        """Test the create_system_notification utility function."""
        notification = create_system_notification(
            user=self.user,
            title="System Alert",
            content="This is a system notification"
        )
        
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.title, "System Alert")
        self.assertEqual(notification.content, "This is a system notification")
        self.assertEqual(notification.notification_type, 'system')
        self.assertIsNone(notification.message)

    def test_mark_all_notifications_read(self):
        """Test the mark_all_notifications_read utility function."""
        # Create some notifications
        message = Message.objects.create(
            sender=self.sender,
            receiver=self.user,
            content="Test message 1"
        )
        create_system_notification(
            user=self.user,
            title="System Alert",
            content="System notification"
        )
        
        # Verify notifications are unread
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 2)
        
        # Mark all as read
        updated_count = mark_all_notifications_read(self.user)
        
        self.assertEqual(updated_count, 2)
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 0)
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=True).count(), 2)

    def test_get_unread_notification_count(self):
        """Test the get_unread_notification_count utility function."""
        # Initially no notifications
        self.assertEqual(get_unread_notification_count(self.user), 0)
        
        # Create some notifications
        message1 = Message.objects.create(
            sender=self.sender,
            receiver=self.user,
            content="Test message 1"
        )
        message2 = Message.objects.create(
            sender=self.sender,
            receiver=self.user,
            content="Test message 2"
        )
        
        self.assertEqual(get_unread_notification_count(self.user), 2)
        
        # Mark one as read
        notification = Notification.objects.first()
        notification.mark_as_read()
        
        self.assertEqual(get_unread_notification_count(self.user), 1)


class IntegrationTest(TestCase):
    """
    Integration tests for the complete notification system.
    """

    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123'
        )
        self.user3 = User.objects.create_user(
            username='user3',
            email='user3@test.com',
            password='testpass123'
        )

    def test_complete_messaging_workflow(self):
        """Test a complete messaging workflow with notifications."""
        # User1 sends a message to User2
        message1 = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content="Hello User2, how are you?"
        )
        
        # Check that User2 received a notification
        self.assertEqual(get_unread_notification_count(self.user2), 1)
        self.assertEqual(get_unread_notification_count(self.user1), 0)
        
        # User2 sends a reply to User1
        message2 = Message.objects.create(
            sender=self.user2,
            receiver=self.user1,
            content="Hi User1, I'm doing great!"
        )
        
        # Check notifications
        self.assertEqual(get_unread_notification_count(self.user1), 1)
        self.assertEqual(get_unread_notification_count(self.user2), 1)
        
        # User1 reads their notification
        mark_all_notifications_read(self.user1)
        self.assertEqual(get_unread_notification_count(self.user1), 0)
        self.assertEqual(get_unread_notification_count(self.user2), 1)
        
        # User3 sends messages to both users
        Message.objects.create(
            sender=self.user3,
            receiver=self.user1,
            content="Hello from User3 to User1"
        )
        Message.objects.create(
            sender=self.user3,
            receiver=self.user2,
            content="Hello from User3 to User2"
        )
        
        # Final notification counts
        self.assertEqual(get_unread_notification_count(self.user1), 1)
        self.assertEqual(get_unread_notification_count(self.user2), 2)
        self.assertEqual(get_unread_notification_count(self.user3), 0)

    def test_notification_content_accuracy(self):
        """Test that notification content accurately reflects the message."""
        message_content = "This is a test message with specific content"
        
        message = Message.objects.create(
            sender=self.user1,
            receiver=self.user2,
            content=message_content
        )
        
        notification = Notification.objects.get(user=self.user2, message=message)
        
        self.assertIn(self.user1.username, notification.title)
        self.assertIn(message_content, notification.content)
        self.assertEqual(notification.notification_type, 'message')
        self.assertFalse(notification.is_read)