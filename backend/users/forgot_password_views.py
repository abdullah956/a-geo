from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import PasswordResetOTP
from .serializers import UserSerializer
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    """
    Step 1: Request password reset - send OTP to email
    """
    try:
        email = request.data.get('email')
        
        if not email:
            return Response(
                {'error': 'Email is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            return Response(
                {'message': 'If the email exists, an OTP has been sent'}, 
                status=status.HTTP_200_OK
            )
        
        # Create OTP for user
        otp = PasswordResetOTP.create_otp_for_user(user)
        
        # Send OTP via email
        if otp.send_otp_email():
            logger.info(f"Password reset OTP sent to {email}")
            return Response(
                {'message': 'OTP sent to your email address'}, 
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Failed to send OTP email'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Error in request_password_reset: {str(e)}")
        return Response(
            {'error': 'An error occurred'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """
    Step 2: Verify OTP code
    """
    try:
        email = request.data.get('email')
        otp_code = request.data.get('otp')
        
        if not email or not otp_code:
            return Response(
                {'error': 'Email and OTP are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid email'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find valid OTP for this user
        try:
            otp = PasswordResetOTP.objects.filter(
                user=user,
                otp_code=otp_code,
                is_used=False
            ).latest('created_at')
            
            if otp.is_valid():
                # Mark OTP as used
                otp.is_used = True
                otp.save()
                
                logger.info(f"OTP verified for {email}")
                return Response(
                    {'message': 'OTP verified successfully'}, 
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Invalid or expired OTP'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except PasswordResetOTP.DoesNotExist:
            return Response(
                {'error': 'Invalid OTP'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error in verify_otp: {str(e)}")
        return Response(
            {'error': 'An error occurred'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """
    Step 3: Reset password with new password
    """
    try:
        email = request.data.get('email')
        otp_code = request.data.get('otp')
        new_password = request.data.get('new_password')
        
        if not all([email, otp_code, new_password]):
            return Response(
                {'error': 'Email, OTP, and new password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(new_password) < 8:
            return Response(
                {'error': 'Password must be at least 8 characters long'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid email'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify OTP was used (should be marked as used in step 2)
        try:
            otp = PasswordResetOTP.objects.filter(
                user=user,
                otp_code=otp_code,
                is_used=True
            ).latest('created_at')
            
            # Check if OTP was used recently (within last 5 minutes)
            if timezone.now() - otp.created_at > timezone.timedelta(minutes=5):
                return Response(
                    {'error': 'OTP session expired'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Reset password
            user.set_password(new_password)
            user.save()
            
            # Invalidate all OTPs for this user
            PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)
            
            logger.info(f"Password reset successful for {email}")
            return Response(
                {'message': 'Password reset successfully'}, 
                status=status.HTTP_200_OK
            )
            
        except PasswordResetOTP.DoesNotExist:
            return Response(
                {'error': 'Invalid OTP or OTP not verified'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"Error in reset_password: {str(e)}")
        return Response(
            {'error': 'An error occurred'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
