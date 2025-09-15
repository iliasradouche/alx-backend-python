import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import os
from datetime import datetime

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all incoming HTTP requests to a file.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Set up logging to file
        self.log_file = os.path.join(settings.BASE_DIR, 'requests.log')
        
        # Configure logging
        logging.basicConfig(
            filename=self.log_file,
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger('request_logger')
        
        # Create file handler specifically for this middleware
        if not self.logger.handlers:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.INFO)
    
    def __call__(self, request):
        # Log the request
        self.log_request(request)
        
        # Process the request
        response = self.get_response(request)
        
        return response
    
    def log_request(self, request):
        """
        Log request details to file
        """
        user = getattr(request, 'user', None)
        user_info = f"User: {user.username if user and user.is_authenticated else 'Anonymous'}"
        
        log_message = f"{request.method} {request.path} - {user_info} - IP: {self.get_client_ip(request)}"
        
        # Write directly to file to ensure logging works
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"{timestamp} - {log_message}\n")
        except Exception as e:
            print(f"Error writing to log file: {e}")
    
    def get_client_ip(self, request):
        """
        Get the client's IP address from the request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip