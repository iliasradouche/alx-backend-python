import logging
from datetime import datetime
import os
from django.conf import settings


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