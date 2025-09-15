from rest_framework.routers import DefaultRouter
from .views import ConversationViewSet, MessageViewSet
from django.urls import path, include
from . import auth

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    path('', include(router.urls)),
    
    # Authentication endpoints
    path('auth/register/', auth.register, name='register'),
    path('auth/logout/', auth.logout, name='logout'),
    path('auth/profile/', auth.user_profile, name='user_profile'),
    path('auth/profile/update/', auth.update_profile, name='update_profile'),
    path('auth/change-password/', auth.change_password, name='change_password'),
]