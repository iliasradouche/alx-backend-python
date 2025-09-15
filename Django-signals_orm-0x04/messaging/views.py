from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.db import transaction
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
