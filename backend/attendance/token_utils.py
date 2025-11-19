"""
Utility functions for QR code token generation and verification
"""
import jwt
import hashlib
import qrcode
import io
import base64
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import AttendanceToken


# Secret key for JWT signing (use Django's SECRET_KEY)
JWT_SECRET = settings.SECRET_KEY
JWT_ALGORITHM = 'HS256'


def generate_token(session, duration_minutes=10, request=None):
    """
    Generate a JWT token for an attendance session
    
    Args:
        session: AttendanceSession instance
        duration_minutes: Token validity duration in minutes
        request: Django request object (optional, for getting frontend URL)
    
    Returns:
        dict: Token data including token string and QR code
    """
    # Token expiration time
    expires_at = timezone.now() + timedelta(minutes=duration_minutes)
    
    # JWT payload
    payload = {
        'session_id': session.id,
        'course_id': session.course.id,
        'course_code': session.course.code,
        'teacher_id': session.teacher.id,
        'issued_at': timezone.now().isoformat(),
        'expires_at': expires_at.isoformat(),
        'type': 'attendance_token'
    }
    
    # Generate JWT token
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    # Generate token hash for storage
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Store token in database
    attendance_token = AttendanceToken.objects.create(
        session=session,
        token=token,
        token_hash=token_hash,
        expires_at=expires_at,
        max_uses=0  # Unlimited uses
    )
    
    # Generate URL for QR code (instead of just token)
    # QR codes are meant to be scanned by mobile devices, so always use network IP
    # Try to get frontend URL from request, but prefer network IP over localhost
    if request:
        # Get the frontend URL from request referer (most reliable)
        referer = request.META.get('HTTP_REFERER', '')
        if referer:
            # Extract base URL from referer
            from urllib.parse import urlparse
            parsed = urlparse(referer)
            frontend_base = f"{parsed.scheme}://{parsed.netloc}"
            
            # If referer is localhost, replace with network IP for mobile access
            if 'localhost' in frontend_base or '127.0.0.1' in frontend_base:
                # Use network IP instead (for mobile scanning)
                frontend_base = 'http://192.168.18.13:3000'
        else:
            # Try to get from Origin header
            origin = request.META.get('HTTP_ORIGIN', '')
            if origin:
                frontend_base = origin
                # If origin is localhost, replace with network IP
                if 'localhost' in frontend_base or '127.0.0.1' in frontend_base:
                    frontend_base = 'http://192.168.18.13:3000'
            else:
                # Use request host to determine frontend URL
                # Backend runs on port 8000, frontend on 3000
                host = request.get_host()
                host_without_port = host.split(':')[0] if ':' in host else host
                
                if host_without_port in ['localhost', '127.0.0.1']:
                    # For QR codes, always use network IP (mobile devices can't access localhost)
                    frontend_base = 'http://192.168.18.13:3000'
                else:
                    # Use the same IP but port 3000 for frontend
                    frontend_base = f"http://{host_without_port}:3000"
    else:
        # Default to network IP for QR codes (mobile scanning)
        frontend_base = 'http://192.168.18.13:3000'
    
    # Create attendance URL with token
    attendance_url = f"{frontend_base}/attendance/qr/{token}"
    
    # Generate QR code with URL
    qr_code_data = generate_qr_code(attendance_url)
    
    return {
        'token': token,
        'token_hash': token_hash,
        'expires_at': expires_at.isoformat(),
        'qr_code': qr_code_data,
        'token_id': attendance_token.id,
        'attendance_url': attendance_url  # Also return URL for reference
    }


def generate_qr_code(data, size=10, border=2):
    """
    Generate QR code image from data
    
    Args:
        data: Data to encode in QR code
        size: QR code size (box_size parameter)
        border: Border size
    
    Returns:
        str: Base64 encoded QR code image
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_base64}"


def verify_token(token_string):
    """
    Verify and decode a JWT token
    
    Args:
        token_string: JWT token string
    
    Returns:
        dict: Decoded token payload if valid, None otherwise
    """
    try:
        # Decode JWT
        payload = jwt.decode(token_string, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Check if token exists in database
        token_hash = hashlib.sha256(token_string.encode()).hexdigest()
        
        try:
            token_obj = AttendanceToken.objects.get(token_hash=token_hash)
            
            # Check if token is valid
            if not token_obj.is_valid:
                return None
            
            # Mark token as used
            token_obj.mark_used()
            
            return payload
            
        except AttendanceToken.DoesNotExist:
            return None
            
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception as e:
        print(f"Token verification error: {e}")
        return None


def deactivate_session_tokens(session):
    """
    Deactivate all tokens for a session
    
    Args:
        session: AttendanceSession instance
    """
    tokens = AttendanceToken.objects.filter(session=session, is_active=True)
    for token in tokens:
        token.deactivate()


def refresh_token(session, old_token_string=None, request=None):
    """
    Refresh/regenerate token for a session
    
    Args:
        session: AttendanceSession instance
        old_token_string: Optional old token to deactivate
        request: Django request object (optional, for getting frontend URL)
    
    Returns:
        dict: New token data
    """
    # Deactivate old token if provided
    if old_token_string:
        token_hash = hashlib.sha256(old_token_string.encode()).hexdigest()
        try:
            old_token = AttendanceToken.objects.get(token_hash=token_hash)
            old_token.deactivate()
        except AttendanceToken.DoesNotExist:
            pass
    
    # Generate new token (pass request to get frontend URL)
    return generate_token(session, request=request)

