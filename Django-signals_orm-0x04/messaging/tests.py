from django.test import TestCase
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from unittest.mock import patch
from .models import Message, Notification
from .signals import (
    create_message_notification,
    mark_message_as_unread,
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