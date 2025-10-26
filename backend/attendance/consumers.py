"""
WebSocket consumers for real-time attendance notifications
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from .models import AttendanceSession

User = get_user_model()
logger = logging.getLogger(__name__)


class AttendanceNotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time attendance session notifications
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.user_group_name = f'attendance_notifications_{self.user_id}'
        
        # Join user-specific group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f'WebSocket connected for user {self.user_id}')
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave user-specific group
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
        logger.info(f'WebSocket disconnected for user {self.user_id}, code: {close_code}')
    
    async def receive(self, text_data):
        """Handle messages received from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'message': 'Connection alive'
                }))
            elif message_type == 'authenticate':
                token = text_data_json.get('token')
                is_authenticated = await self.authenticate_user(token)
                await self.send(text_data=json.dumps({
                    'type': 'auth_result',
                    'authenticated': is_authenticated
                }))
        except json.JSONDecodeError:
            logger.error('Invalid JSON received from WebSocket')
        except Exception as e:
            logger.error(f'Error processing WebSocket message: {e}')
    
    async def attendance_session_started(self, event):
        """Send attendance session started notification to user"""
        session_data = event['session_data']
        
        await self.send(text_data=json.dumps({
            'type': 'attendance_session_started',
            'session': session_data,
            'message': f'New attendance session started: {session_data.get("title", "Unknown")}'
        }))
        logger.info(f'Sent session started notification to user {self.user_id}')
    
    async def attendance_session_ended(self, event):
        """Send attendance session ended notification to user"""
        session_data = event['session_data']
        
        await self.send(text_data=json.dumps({
            'type': 'attendance_session_ended',
            'session': session_data,
            'message': f'Attendance session ended: {session_data.get("title", "Unknown")}'
        }))
        logger.info(f'Sent session ended notification to user {self.user_id}')
    
    async def attendance_marked(self, event):
        """Send attendance marked notification to user"""
        attendance_data = event['attendance_data']
        
        await self.send(text_data=json.dumps({
            'type': 'attendance_marked',
            'attendance': attendance_data,
            'message': 'Your attendance has been marked successfully'
        }))
        logger.info(f'Sent attendance marked notification to user {self.user_id}')
    
    @database_sync_to_async
    def authenticate_user(self, token):
        """Authenticate user using JWT token"""
        try:
            if not token:
                return False
            
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Decode and validate token
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            # Verify user exists and matches the WebSocket user_id
            return str(user_id) == str(self.user_id)
        except Exception as e:
            logger.error(f'Authentication error: {e}')
            return False


class AttendanceBroadcastConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for broadcasting attendance updates to all connected users
    """
    
    async def connect(self):
        """Handle WebSocket connection for broadcast channel"""
        self.broadcast_group_name = 'attendance_broadcast'
        
        # Join broadcast group
        await self.channel_layer.group_add(
            self.broadcast_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info('WebSocket connected to broadcast channel')
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection from broadcast channel"""
        # Leave broadcast group
        await self.channel_layer.group_discard(
            self.broadcast_group_name,
            self.channel_name
        )
        logger.info(f'WebSocket disconnected from broadcast channel, code: {close_code}')
    
    async def receive(self, text_data):
        """Handle messages received from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'message': 'Broadcast connection alive'
                }))
        except json.JSONDecodeError:
            logger.error('Invalid JSON received from broadcast WebSocket')
        except Exception as e:
            logger.error(f'Error processing broadcast WebSocket message: {e}')
    
    async def broadcast_session_update(self, event):
        """Broadcast session update to all connected users"""
        update_data = event['update_data']
        
        await self.send(text_data=json.dumps({
            'type': 'session_update',
            'data': update_data,
            'message': 'Attendance session updated'
        }))
        logger.info('Broadcasted session update to all users')
