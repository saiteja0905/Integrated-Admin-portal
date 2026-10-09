# Abstraction layer for sending SMS, WhatsApp & Push notifications
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)

# Mock message log store for demo/testing verification
OUTBOUND_MESSAGES = []

class NotificationService:
    """
    Notification abstraction layer.
    Allows sending Parent SMS/WhatsApp alerts and Sanyuth system notifications.
    Can be hooked into Twilio, WhatsApp Business API, or Firebase Cloud Messaging.
    """

    def __init__(self, provider: str = "mock"):
        self.provider = provider

    async def send_parent_booking_sms(
        self,
        parent_phone: str,
        parent_name: str,
        service_name: str,
        worker_name: str,
        otp: str,
        language: str = "English"
    ) -> Dict[str, Any]:
        """Send booking confirmation SMS to parent with OTP."""
        templates = {
            "Telugu": f"నమస్కారం {parent_name}, మీ కోసం {service_name} బుకింగ్ నిర్ధారించబడింది. వర్కర్: {worker_name}. మీ OTP: {otp}. సహాయానికి యాప్‌ని సందర్శించండి.",
            "Hindi": f"नमस्ते {parent_name}, आपके लिए {service_name} की बुकिंग कन्फर्म हो गई है। कार्यकर्ता: {worker_name}। आपका OTP: {otp}।",
            "English": f"Hello {parent_name}, your {service_name} booking is confirmed with {worker_name}. Your arrival verification OTP is: {otp}."
        }
        msg_text = templates.get(language, templates["English"])

        msg_record = {
            "id": str(uuid.uuid4()),
            "type": "parent_booking_sms",
            "to_phone": parent_phone,
            "parent_name": parent_name,
            "content": msg_text,
            "otp": otp,
            "language": language,
            "status": "sent",
            "sent_at": datetime.now(timezone.utc).isoformat()
        }
        OUTBOUND_MESSAGES.append(msg_record)
        logger.info(f"📱 [NOTIFICATION SERVICE] Sent Parent SMS to {parent_phone}: {msg_text}")
        return msg_record

    async def send_status_update_whatsapp(
        self,
        parent_phone: str,
        status: str,
        worker_name: str,
        language: str = "English"
    ) -> Dict[str, Any]:
        """Send booking status update WhatsApp message to parent."""
        status_labels = {
            "on_the_way": "Worker is on the way 🚗",
            "arrived": "Worker has arrived at your location 📍",
            "started": "Work has officially started 🔧",
            "completed": "Work is completed! 🎉"
        }
        status_text = status_labels.get(status, f"Status updated: {status}")
        msg_text = f"Sanyuth Update for {parent_phone}: {worker_name} - {status_text}"

        msg_record = {
            "id": str(uuid.uuid4()),
            "type": "parent_whatsapp_status",
            "to_phone": parent_phone,
            "content": msg_text,
            "status": "sent",
            "sent_at": datetime.now(timezone.utc).isoformat()
        }
        OUTBOUND_MESSAGES.append(msg_record)
        logger.info(f"💬 [NOTIFICATION SERVICE] Sent Parent WhatsApp to {parent_phone}: {msg_text}")
        return msg_record

notification_service = NotificationService()
