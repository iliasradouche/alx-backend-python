from django.urls import path
from . import views

app_name = "messaging"

urlpatterns = [
    # User deletion URLs
    path("delete-account/", views.delete_user, name="delete_user"),
    path("delete-account/stats/", views.delete_user_stats, name="delete_user_stats"),
    path("account-deleted/", views.user_deletion_success, name="user_deletion_success"),
    
    # Threaded conversation URLs
    path("", views.conversations_list, name="conversations_list"),
    path("thread/<int:message_id>/", views.thread_view, name="thread_view"),
    path("send/", views.send_message, name="send_message"),
    path("api/thread/<int:message_id>/", views.get_thread_json, name="get_thread_json"),
]
