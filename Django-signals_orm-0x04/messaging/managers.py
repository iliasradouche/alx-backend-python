from django.db import models
from django.contrib.auth.models import User


class UnreadMessagesManager(models.Manager):
    """
    Custom manager for filtering unread messages with optimized queries.
    Provides methods to efficiently handle unread message operations.
    """
    
    def unread_for_user(self, user):
        """
        Get all unread messages for a specific user (as receiver).
        Uses select_related and only() for query optimization.
        
        Args:
            user: User instance to filter messages for
            
        Returns:
            QuerySet of unread messages with optimized fields
        """
        return self.filter(
            receiver=user,
            is_read=False
        ).select_related(
            'sender',
            'parent_message'
        ).only(
            'id',
            'content', 
            'timestamp',
            'is_read',
            'parent_message_id',
            'sender__username',
            'sender__first_name',
            'sender__last_name'
        ).order_by('-timestamp')
    
    def unread_count_for_user(self, user):
        """
        Get count of unread messages for a specific user.
        
        Args:
            user: User instance to count messages for
            
        Returns:
            Integer count of unread messages
        """
        return self.filter(
            receiver=user,
            is_read=False
        ).count()
    
    def mark_as_read_for_user(self, user, message_ids=None):
        """
        Mark messages as read for a specific user.
        
        Args:
            user: User instance
            message_ids: Optional list of specific message IDs to mark as read.
                        If None, marks all unread messages for the user as read.
                        
        Returns:
            Integer count of messages that were updated
        """
        queryset = self.filter(
            receiver=user,
            is_read=False
        )
        
        if message_ids:
            queryset = queryset.filter(id__in=message_ids)
            
        return queryset.update(is_read=True)