from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # User deletion URLs
    path('delete-account/', views.delete_user, name='delete_user'),
    path('delete-account/stats/', views.delete_user_stats, name='delete_user_stats'),
    path('account-deleted/', views.user_deletion_success, name='user_deletion_success'),
]