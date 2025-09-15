from rest_framework import permissions
from rest_framework.permissions import BasePermission
from django.db import models
from .models import Conversation, Message


class IsOwnerOrReadOnly(BasePermission):
    """Custom permission to only allow owners of an object to edit it."""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user


class IsParticipantInConversation(BasePermission):
    """Custom permission to only allow participants in a conversation to access it."""
    
    def has_object_permission(self, request, view, obj):
        # Check if the user is a participant in the conversation
        if hasattr(obj, 'participants'):
            return request.user in obj.participants.all()
        
        # For conversation objects, check if user is in participants
        if isinstance(obj, Conversation):
            return request.user in obj.participants.all()
        
        return False


class IsMessageParticipant(BasePermission):
    """Custom permission to only allow message participants (sender/receiver) to access messages."""
    
    def has_permission(self, request, view):
        # Allow authenticated users to create messages
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Check if the user is either the sender or receiver of the message
        if isinstance(obj, Message):
            return (obj.sender == request.user or 
                   obj.receiver == request.user)
        
        return False


class CanAccessConversation(BasePermission):
    """Permission to check if user can access a conversation based on message participation."""
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # For conversations, check if user has any messages in this conversation
        if isinstance(obj, Conversation):
            return Message.objects.filter(
                conversation=obj
            ).filter(
                models.Q(sender=request.user) | models.Q(receiver=request.user)
            ).exists()
        
        return False


class IsOwnerOrParticipant(BasePermission):
    """Permission that allows access to owners or participants."""
    
    def has_object_permission(self, request, view, obj):
        # Check if user is the owner
        if hasattr(obj, 'owner') and obj.owner == request.user:
            return True
        
        # Check if user is a participant (for messages)
        if isinstance(obj, Message):
            return (obj.sender == request.user or obj.receiver == request.user)
        
        # Check if user is a participant (for conversations)
        if isinstance(obj, Conversation):
            return request.user in obj.participants.all()
        
        return False


class CanModifyOwnContent(BasePermission):
    """Permission that allows users to modify only their own content."""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for participants
        if request.method in permissions.SAFE_METHODS:
            if isinstance(obj, Message):
                return (obj.sender == request.user or obj.receiver == request.user)
            elif isinstance(obj, Conversation):
                return request.user in obj.participants.all()
        
        # Write permissions only for owners/creators
        if hasattr(obj, 'sender'):
            return obj.sender == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class MessagePermission(BasePermission):
    """Comprehensive permission class for message operations."""
    
    def has_permission(self, request, view):
        # Must be authenticated
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Message):
            return False
        
        # Users can read messages they sent or received
        if request.method in permissions.SAFE_METHODS:
            return (obj.sender == request.user or obj.receiver == request.user)
        
        # Users can only modify (update/delete) messages they sent
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return obj.sender == request.user
        
        return False


class IsParticipantOfConversation(BasePermission):
    """
    Custom permission class to control access to conversations and messages.
    - Allow only authenticated users to access the API
    - Allow only participants in a conversation to send, view, update and delete messages
    """
    
    def has_permission(self, request, view):
        """Check if user is authenticated before allowing any access."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user is a participant in the conversation for object-level permissions."""
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Handle Message objects
        if isinstance(obj, Message):
            # Check if user is either sender or receiver of the message
            if obj.sender == request.user or obj.receiver == request.user:
                return True
            
            # Also check if user is a participant in the conversation
            if hasattr(obj, 'conversation') and obj.conversation:
                return request.user in obj.conversation.participants.all()
            
            return False
        
        # Handle Conversation objects
        if isinstance(obj, Conversation):
            return request.user in obj.participants.all()
        
        return False


class ConversationPermission(BasePermission):
    """Comprehensive permission class for conversation operations."""
    
    def has_permission(self, request, view):
        # Must be authenticated
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if not isinstance(obj, Conversation):
            return False
        
        # Check if user is a participant in the conversation
        is_participant = request.user in obj.participants.all()
        
        # Users can read conversations they participate in
        if request.method in permissions.SAFE_METHODS:
            return is_participant
        
        # Users can modify conversations they created or are admin of
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            return (hasattr(obj, 'created_by') and obj.created_by == request.user) or is_participant
        
        return False