from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db import models
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from .permissions import ConversationPermission, MessagePermission, IsMessageParticipant, IsParticipantOfConversation
from .pagination import MessagePagination, ConversationPagination
from .filters import MessageFilter, ConversationFilter

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsParticipantOfConversation]
    pagination_class = ConversationPagination
    filterset_class = ConversationFilter
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['participants__email']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        return Conversation.objects.filter(participants=user)

    def check_conversation_access(self, conversation_id):
        """Check if user has access to the conversation."""
        try:
            conversation = get_object_or_404(Conversation, id=conversation_id)
            if self.request.user not in conversation.participants.all():
                return Response(
                    {'error': 'Access denied to this conversation'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return conversation
        except Conversation.DoesNotExist:
            return Response(
                {'error': 'Conversation not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to add access control."""
        conversation_id = kwargs.get('pk')
        access_check = self.check_conversation_access(conversation_id)
        if isinstance(access_check, Response):
            return access_check
        
        serializer = self.get_serializer(access_check)
        return Response(serializer.data)

    def perform_create(self, serializer):
        conversation = serializer.save()
        if self.request.user not in conversation.participants.all():
            conversation.participants.add(self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsParticipantOfConversation])
    def send_message(self, request, pk=None):
        conversation_id = pk
        access_check = self.check_conversation_access(conversation_id)
        if isinstance(access_check, Response):
            return access_check
        
        conversation = access_check
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(conversation=conversation, sender=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(cache_page(60), name='list')
class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsParticipantOfConversation]
    pagination_class = MessagePagination
    filterset_class = MessageFilter
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['sender__email', 'message_body']
    ordering_fields = ['sent_at']
    ordering = ['-sent_at']

    def get_queryset(self):
        user = self.request.user
        # Users can only see messages they sent or received
        return Message.objects.filter(
            models.Q(sender=user) | models.Q(receiver=user)
        ).select_related('sender', 'receiver', 'conversation')

    def check_message_access(self, message_id):
        """Check if user has access to the message."""
        try:
            message = get_object_or_404(Message, id=message_id)
            if (message.sender != self.request.user and 
                message.receiver != self.request.user):
                return Response(
                    {'error': 'Access denied to this message'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return message
        except Message.DoesNotExist:
            return Response(
                {'error': 'Message not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to add access control."""
        message_id = kwargs.get('pk')
        access_check = self.check_message_access(message_id)
        if isinstance(access_check, Response):
            return access_check
        
        serializer = self.get_serializer(access_check)
        return Response(serializer.data)

    def perform_create(self, serializer):
        # Check if conversation_id is provided and validate access
        conversation_id = self.request.data.get('conversation_id')
        if conversation_id:
            try:
                conversation = get_object_or_404(Conversation, id=conversation_id)
                if self.request.user not in conversation.participants.all():
                    return Response(
                        {'error': 'Access denied to this conversation'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                serializer.save(sender=self.request.user, conversation=conversation)
            except Conversation.DoesNotExist:
                return Response(
                    {'error': 'Conversation not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            serializer.save(sender=self.request.user)