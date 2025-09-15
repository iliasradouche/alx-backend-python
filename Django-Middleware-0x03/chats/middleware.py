import logging
from datetime import datetime, timedelta
import os
from django.conf import settings
from django.http import JsonResponse
from collections import defaultdict


class RequestLoggingMiddleware:
    """
    Middleware to log each user's requests to a file with timestamp, user, and request path.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Set up logging configuration
        log_file_path = os.path.join(settings.BASE_DIR, 'requests.log')
        
        # Configure logger
        self.logger = logging.getLogger('request_logger')
        self.logger.setLevel(logging.INFO)
        
        # Create file handler if it doesn't exist
        if not self.logger.handlers:
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter('%(message)s')
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            self.logger.addHandler(file_handler)
    
    def __call__(self, request):
        # Debug print to console
        print(f"DEBUG: Middleware called for path: {request.path}")
        
        # Get user information
        if request.user.is_authenticated:
            user = request.user.username
        else:
            user = 'Anonymous'
        
        # Log the request information
        log_message = f"{datetime.now()} - User: {user} - Path: {request.path}"
        self.logger.info(log_message)
        print(f"DEBUG: Logged message: {log_message}")
        
        # Process the request
        response = self.get_response(request)
        
        return response


class RestrictAccessByTimeMiddleware:
    """
    Middleware to restrict access to the messaging app during certain hours.
    Access is only allowed between 9 AM and 6 PM.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        from django.http import HttpResponseForbidden
        
        # Get current hour (24-hour format)
        current_hour = datetime.now().hour
        
        # Check if current time is outside allowed hours (9 AM to 6 PM)
        # 9 AM = 9, 6 PM = 18
        if current_hour < 9 or current_hour >= 18:
            return HttpResponseForbidden(
                "<h1>Access Denied</h1>"
                "<p>The messaging app is only accessible between 9 AM and 6 PM.</p>"
                f"<p>Current time: {datetime.now().strftime('%I:%M %p')}</p>"
            )
        
        # Process the request if within allowed hours
        response = self.get_response(request)
        return response


class OffensiveLanguageMiddleware:
    """
    Middleware to limit the number of chat messages a user can send within a certain time window,
    based on their IP address. Limits to 5 messages per minute.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Dictionary to store IP addresses and their request timestamps
        # Format: {ip_address: [timestamp1, timestamp2, ...]}
        self.ip_requests = defaultdict(list)
        self.max_requests = 5  # Maximum requests per time window
        self.time_window = timedelta(minutes=1)  # 1 minute time window
    
    def __call__(self, request):
        # Only apply rate limiting to POST requests (chat messages)
        if request.method == 'POST':
            # Get client IP address
            ip_address = self.get_client_ip(request)
            current_time = datetime.now()
            
            # Clean old requests outside the time window
            self.clean_old_requests(ip_address, current_time)
            
            # Check if the IP has exceeded the rate limit
            if len(self.ip_requests[ip_address]) >= self.max_requests:
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'message': f'You can only send {self.max_requests} messages per minute. Please wait before sending another message.',
                    'retry_after': 60  # seconds
                }, status=429)  # HTTP 429 Too Many Requests
            
            # Add current request timestamp
            self.ip_requests[ip_address].append(current_time)
        
        # Process the request
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """
        Get the client's IP address from the request.
        Handles cases where the request comes through a proxy.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP if there are multiple (comma-separated)
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def clean_old_requests(self, ip_address, current_time):
        """
        Remove request timestamps that are outside the current time window.
        """
        cutoff_time = current_time - self.time_window
        self.ip_requests[ip_address] = [
            timestamp for timestamp in self.ip_requests[ip_address]
            if timestamp > cutoff_time
        ]


class RolePermissionMiddleware:
    """
    Middleware to check user's role before allowing access to specific actions.
    Only allows access for users with 'admin' or 'moderator' roles.
    Returns 403 Forbidden for unauthorized users.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Define allowed roles
        self.allowed_roles = ['admin', 'moderator']
    
    def __call__(self, request):
        # Check if user is authenticated
        if request.user.is_authenticated:
            # Get user's role - assuming role is stored in user profile or groups
            user_role = self.get_user_role(request.user)
            
            # Check if user has required role
            if user_role not in self.allowed_roles:
                return JsonResponse({
                    'error': 'Access denied',
                    'message': 'You do not have permission to access this resource. Admin or moderator role required.',
                    'required_roles': self.allowed_roles,
                    'user_role': user_role
                }, status=403)  # HTTP 403 Forbidden
        else:
            # User is not authenticated
            return JsonResponse({
                'error': 'Authentication required',
                'message': 'You must be logged in to access this resource.'
            }, status=403)  # HTTP 403 Forbidden
        
        # Process the request if user has proper role
        response = self.get_response(request)
        return response
    
    def get_user_role(self, user):
        """
        Get the user's role. This method can be customized based on how roles are stored.
        Common approaches:
        1. User groups: user.groups.first().name
        2. User profile field: user.profile.role
        3. Custom user model field: user.role
        """
        # Method 1: Check if user is superuser (admin)
        if user.is_superuser:
            return 'admin'
        
        # Method 2: Check user groups
        if user.groups.exists():
            # Get the first group name as role
            group_name = user.groups.first().name.lower()
            return group_name
        
        # Method 3: Check if user has staff status (could be moderator)
        if user.is_staff:
            return 'moderator'
        
        # Default role for regular users
        return 'user'