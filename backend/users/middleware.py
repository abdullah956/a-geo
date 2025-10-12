import logging
import time
from django.utils.deprecation import MiddlewareMixin

# Get logger instances
api_logger = logging.getLogger('api')
lms_logger = logging.getLogger('lms')


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all API requests and responses
    """
    
    def process_request(self, request):
        # Log incoming request
        if request.path.startswith('/api/'):
            api_logger.info(f"INCOMING REQUEST: {request.method} {request.path} from IP: {self.get_client_ip(request)}")
            api_logger.info(f"Headers: {dict(request.headers)}")
            if hasattr(request, 'body') and request.body:
                api_logger.info(f"Request Body: {request.body.decode('utf-8', errors='ignore')}")
            
            # Store start time for response time calculation
            request._start_time = time.time()
    
    def process_response(self, request, response):
        # Log outgoing response
        if request.path.startswith('/api/'):
            response_time = time.time() - getattr(request, '_start_time', 0)
            
            api_logger.info(f"OUTGOING RESPONSE: {request.method} {request.path} - Status: {response.status_code} - Time: {response_time:.3f}s")
            
            if hasattr(response, 'content') and response.content:
                # Log response content (truncated for large responses)
                content = response.content.decode('utf-8', errors='ignore')
                if len(content) > 500:
                    content = content[:500] + "... [truncated]"
                api_logger.info(f"Response Content: {content}")
            
            lms_logger.debug(f"API Request completed: {request.method} {request.path} in {response_time:.3f}s")
        
        return response
    
    def get_client_ip(self, request):
        """
        Get the client IP address from the request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
