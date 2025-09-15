import django_filters
from django.db import models
from django.contrib.auth import get_user_model
from .models import Message, Conversation

User = get_user_model()


class MessageFilter(django_filters.FilterSet):
    """
    Filter class for Message model.
    Allows filtering by sender, conversation, and time range.
    """
    sender = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        field_name='sender',
        help_text='Filter messages by sender user ID'
    )
    
    conversation = django_filters.ModelChoiceFilter(
        queryset=Conversation.objects.all(),
        field_name='conversation',
        help_text='Filter messages by conversation ID'
    )
    
    # Time range filtering
    sent_after = django_filters.DateTimeFilter(
        field_name='sent_at',
        lookup_expr='gte',
        help_text='Filter messages sent after this datetime (YYYY-MM-DD HH:MM:SS)'
    )
    
    sent_before = django_filters.DateTimeFilter(
        field_name='sent_at',
        lookup_expr='lte',
        help_text='Filter messages sent before this datetime (YYYY-MM-DD HH:MM:SS)'
    )
    
    # Date range filtering (without time)
    date_after = django_filters.DateFilter(
        field_name='sent_at',
        lookup_expr='date__gte',
        help_text='Filter messages sent after this date (YYYY-MM-DD)'
    )
    
    date_before = django_filters.DateFilter(
        field_name='sent_at',
        lookup_expr='date__lte',
        help_text='Filter messages sent before this date (YYYY-MM-DD)'
    )
    
    # Content search
    message_body = django_filters.CharFilter(
        field_name='message_body',
        lookup_expr='icontains',
        help_text='Search messages containing this text'
    )
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('sent_at', 'sent_at'),
        ),
        field_labels={
            'sent_at': 'Sent Date',
        },
        help_text='Order by: sent_at, -sent_at'
    )
    
    class Meta:
        model = Message
        fields = {
            'sender': ['exact'],
            'conversation': ['exact'],
            'message_body': ['icontains'],
            'sent_at': ['gte', 'lte', 'date__gte', 'date__lte'],
        }


class ConversationFilter(django_filters.FilterSet):
    """
    Filter class for Conversation model.
    Allows filtering by participants and time range.
    """
    participants = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        field_name='participants',
        help_text='Filter conversations by participant user IDs'
    )
    
    # Time range filtering
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        help_text='Filter conversations created after this datetime'
    )
    
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        help_text='Filter conversations created before this datetime'
    )
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created_at'),
        ),
        field_labels={
            'created_at': 'Creation Date',
        },
        help_text='Order by: created_at, -created_at'
    )
    
    class Meta:
        model = Conversation
        fields = {
            'participants': ['exact'],
            'created_at': ['gte', 'lte'],
        }