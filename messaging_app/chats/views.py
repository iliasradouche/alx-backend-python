from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from .models import Conversation, Message, User
from .serializers import ConversationSerializer, MessageSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all().prefetch_related("participants", "messages")
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Optionally list only conversations the user participates in
        user = self.request.user
        return Conversation.objects.filter(participants=user)

    def perform_create(self, serializer):
        conversation = serializer.save()
        # Optionally add the creator as a participant if not already added
        if self.request.user not in conversation.participants.all():
            conversation.participants.add(self.request.user)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def send_message(self, request, pk=None):
        conversation = self.get_object()
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(conversation=conversation, sender=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all().select_related("conversation", "sender")
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Optionally filter messages to those in conversations the user participates in
        user = self.request.user
        return Message.objects.filter(conversation__participants=user)

    def perform_create(self, serializer):
        # Requires conversation and sender in request data
        serializer.save(sender=self.request.user)
