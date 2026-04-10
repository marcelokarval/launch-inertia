"""
WebSocket consumers for real-time notifications.

Uses Django Channels for WebSocket support.
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time notifications.

    Clients connect to receive instant notification updates.
    """

    async def connect(self):
        """Handle WebSocket connection."""
        user = self.scope.get("user")

        if not user or not user.is_authenticated:
            await self.close()
            return

        # Create a group for this user
        self.room_group_name = f"notifications_{user.id}"

        # Join the user's notification group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages."""
        # Currently we don't expect client-to-server messages
        # but this could be used for marking notifications as read
        try:
            data = json.loads(text_data)
            action = data.get("action")

            if action == "mark_read":
                notification_id = data.get("notification_id")
                # Handle mark as read via WebSocket
                pass

        except json.JSONDecodeError:
            pass

    async def notification_message(self, event):
        """
        Handle notification messages from the channel layer.

        Called when a notification is sent to this user's group.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "notification": event["notification"],
                }
            )
        )

    async def notification_count(self, event):
        """
        Handle unread count updates.
        """
        await self.send(
            text_data=json.dumps(
                {
                    "type": "count",
                    "unread_count": event["count"],
                }
            )
        )


def send_notification_to_user(user_id: int, notification_data: dict):
    """
    Send a notification to a specific user via WebSocket.

    Usage:
        from apps.notifications.consumers import send_notification_to_user

        send_notification_to_user(user.id, {
            "id": notification.public_id,
            "title": notification.title,
            "body": notification.body,
            "type": notification.notification_type,
        })
    """
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    group_name = f"notifications_{user_id}"

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "notification_message",
            "notification": notification_data,
        },
    )
