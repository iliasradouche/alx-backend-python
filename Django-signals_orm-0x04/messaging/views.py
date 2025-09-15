from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.db import transaction
from .models import Message
import json


@login_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def delete_user(request):
    """
    View to handle user account deletion.

    GET: Display confirmation page
    POST: Process the deletion request

    Args:
        request: HTTP request object

    Returns:
        HttpResponse: Rendered template or redirect response
    """
    if request.method == "GET":
        # Display confirmation page
        context = {
            "user": request.user,
            "message_count": request.user.sent_messages.count()
            + request.user.received_messages.count(),
            "notification_count": request.user.notifications.count(),
        }
        return render(request, "messaging/delete_user_confirm.html", context)

    elif request.method == "POST":
        # Process deletion request
        try:
            # Check if this is an AJAX request
            is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

            # Get confirmation from POST data
            if is_ajax:
                data = json.loads(request.body)
                confirm_deletion = data.get("confirm_deletion", False)
                password_confirmation = data.get("password", "")
            else:
                confirm_deletion = request.POST.get("confirm_deletion") == "true"
                password_confirmation = request.POST.get("password", "")

            # Validate confirmation
            if not confirm_deletion:
                error_msg = "You must confirm the deletion to proceed."
                if is_ajax:
                    return JsonResponse(
                        {"success": False, "error": error_msg}, status=400
                    )
                messages.error(request, error_msg)
                return redirect("delete_user")

            # Validate password (optional security measure)
            if password_confirmation and not request.user.check_password(
                password_confirmation
            ):
                error_msg = "Invalid password confirmation."
                if is_ajax:
                    return JsonResponse(
                        {"success": False, "error": error_msg}, status=400
                    )
                messages.error(request, error_msg)
                return redirect("delete_user")

            # Store user info before deletion
            user_id = request.user.id
            username = request.user.username

            # Use transaction to ensure atomicity
            with transaction.atomic():
                # Get the user object
                user = request.user

                # Log out the user before deletion
                logout(request)

                # Delete the user (this will trigger the post_delete signal)
                user.delete()

            # Success response
            success_msg = f"Account '{username}' has been successfully deleted."

            if is_ajax:
                return JsonResponse(
                    {"success": True, "message": success_msg, "redirect_url": "/"}
                )
            else:
                messages.success(request, success_msg)
                return redirect("/")

        except Exception as e:
            error_msg = f"An error occurred while deleting the account: {str(e)}"

            if is_ajax:
                return JsonResponse({"success": False, "error": error_msg}, status=500)
            else:
                messages.error(request, error_msg)
                return redirect("delete_user")


@login_required
def delete_user_stats(request):
    """
    API endpoint to get user deletion statistics.

    Returns:
        JsonResponse: Statistics about data that will be deleted
    """
    try:
        user = request.user

        # Count related data
        sent_messages = user.sent_messages.count()
        received_messages = user.received_messages.count()
        total_messages = sent_messages + received_messages

        notifications = user.notifications.count()

        # Count message histories where user was the editor
        from .models import MessageHistory

        message_histories = MessageHistory.objects.filter(edited_by=user).count()

        stats = {
            "username": user.username,
            "email": user.email,
            "date_joined": user.date_joined.isoformat(),
            "sent_messages": sent_messages,
            "received_messages": received_messages,
            "total_messages": total_messages,
            "notifications": notifications,
            "message_histories": message_histories,
            "total_data_points": total_messages + notifications + message_histories,
        }

        return JsonResponse({"success": True, "stats": stats})

    except Exception as e:
        return JsonResponse(
            {"success": False, "error": f"Failed to retrieve user stats: {str(e)}"},
            status=500,
        )


def user_deletion_success(request):
    """
    Success page displayed after user deletion.

    Args:
        request: HTTP request object

    Returns:
        HttpResponse: Rendered success template
    """
    return render(request, "messaging/user_deleted_success.html")


@login_required
def conversations_list(request):
    """
    Display all conversations for the current user with threading support.
    """
    conversations = Message.get_conversations_optimized(request.user)
    
    # Group messages by conversation threads
    conversation_threads = {}
    for message in conversations:
        root = message.get_thread_root()
        if root.id not in conversation_threads:
            conversation_threads[root.id] = {
                'root_message': root,
                'participants': set([root.sender, root.receiver]),
                'last_activity': root.timestamp,
                'message_count': 1
            }
        else:
            conversation_threads[root.id]['participants'].update([message.sender, message.receiver])
            if message.timestamp > conversation_threads[root.id]['last_activity']:
                conversation_threads[root.id]['last_activity'] = message.timestamp
            conversation_threads[root.id]['message_count'] += 1
    
    # Sort by last activity
    sorted_conversations = sorted(
        conversation_threads.values(),
        key=lambda x: x['last_activity'],
        reverse=True
    )
    
    context = {
        'conversations': sorted_conversations,
        'user': request.user
    }
    return render(request, 'messaging/conversations_list.html', context)


@login_required
def thread_view(request, message_id):
    """
    Display a complete message thread with all replies.
    """
    root_message = get_object_or_404(Message, id=message_id)
    
    # Ensure user has permission to view this thread
    if request.user not in [root_message.sender, root_message.receiver]:
        raise PermissionDenied("You don't have permission to view this conversation.")
    
    # Get the actual root of the thread
    thread_root = root_message.get_thread_root()
    
    # Get all messages in the thread with optimized queries
    thread_messages = Message.get_thread_optimized(thread_root.id)
    
    # Build the threaded structure
    threaded_messages = thread_root.get_all_replies_recursive()
    
    context = {
        'root_message': thread_root,
        'threaded_messages': threaded_messages,
        'thread_messages': thread_messages,
        'user': request.user
    }
    return render(request, 'messaging/thread_view.html', context)


@login_required
@csrf_protect
@require_http_methods(["POST"])
def send_message(request):
    """
    Send a new message or reply to an existing message.
    """
    try:
        data = json.loads(request.body)
        receiver_id = data.get('receiver_id')
        content = data.get('content', '').strip()
        parent_message_id = data.get('parent_message_id')
        
        if not content:
            return JsonResponse({'success': False, 'error': 'Message content cannot be empty'})
        
        if not receiver_id:
            return JsonResponse({'success': False, 'error': 'Receiver is required'})
        
        receiver = get_object_or_404(User, id=receiver_id)
        parent_message = None
        
        if parent_message_id:
            parent_message = get_object_or_404(Message, id=parent_message_id)
            # Ensure user has permission to reply to this message
            if request.user not in [parent_message.sender, parent_message.receiver]:
                raise PermissionDenied("You don't have permission to reply to this message.")
        
        # Create the message
        message = Message.objects.create(
            sender=request.user,
            receiver=receiver,
            content=content,
            parent_message=parent_message
        )
        
        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'message': {
                'id': message.id,
                'content': message.content,
                'sender': message.sender.username,
                'receiver': message.receiver.username,
                'timestamp': message.timestamp.isoformat(),
                'is_reply': message.is_reply(),
                'parent_message_id': message.parent_message.id if message.parent_message else None
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def get_thread_json(request, message_id):
    """
    API endpoint to get thread data in JSON format for AJAX requests.
    """
    try:
        root_message = get_object_or_404(Message, id=message_id)
        
        # Ensure user has permission
        if request.user not in [root_message.sender, root_message.receiver]:
            raise PermissionDenied("You don't have permission to view this conversation.")
        
        thread_root = root_message.get_thread_root()
        threaded_messages = thread_root.get_all_replies_recursive()
        
        def serialize_thread(thread_data):
            result = []
            for item in thread_data:
                message = item['message']
                serialized = {
                    'id': message.id,
                    'content': message.content,
                    'sender': message.sender.username,
                    'receiver': message.receiver.username,
                    'timestamp': message.timestamp.isoformat(),
                    'depth': item['depth'],
                    'is_read': message.is_read,
                    'replies': serialize_thread(item['replies'])
                }
                result.append(serialized)
            return result
        
        return JsonResponse({
            'success': True,
            'root_message': {
                'id': thread_root.id,
                'content': thread_root.content,
                'sender': thread_root.sender.username,
                'receiver': thread_root.receiver.username,
                'timestamp': thread_root.timestamp.isoformat(),
                'is_read': thread_root.is_read
            },
            'replies': serialize_thread(threaded_messages)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
