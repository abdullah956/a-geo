"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
import django
import threading
import time
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Initialize Django
django.setup()

# Import routing after Django is set up
import attendance.routing

django_asgi_app = get_asgi_application()

# Start auto-end scheduler in background thread
def start_scheduler():
    """Start the auto-end scheduler in a background thread"""
    try:
        from attendance.auto_end_scheduler import run_scheduler
        print("Starting auto-end scheduler...")
        run_scheduler(check_interval=60)  # Check every minute
    except Exception as e:
        print(f"Failed to start scheduler: {e}")

# Start scheduler in daemon thread
scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
scheduler_thread.start()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                attendance.routing.websocket_urlpatterns
            )
        )
    ),
})
