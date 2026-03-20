from app.config.settings import settings
from app.utils.logger import logger

class NotificationService:
    def __init__(self):
        self.twilio_client = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            try:
                from twilio.rest import Client
                self.twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                logger.info("Twilio SMS service initialized")
            except Exception as e:
                logger.warning(f"Twilio init failed: {e}")

    async def send_sms_alert(self, phone_number: str, message: str) -> bool:
        if not self.twilio_client:
            logger.info(f"[SMS MOCK] To: {phone_number} | Msg: {message}")
            return True
        try:
            self.twilio_client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number,
            )
            logger.info(f"SMS sent to {phone_number}")
            return True
        except Exception as e:
            logger.error(f"SMS failed: {e}")
            return False

    async def send_critical_alert(self, patient_name: str, risk_score: int, phone_numbers: list) -> None:
        message = f"🚨 CRITICAL SEPSIS ALERT — {patient_name} | Risk Score: {risk_score}/100 | Immediate action required. SepsisShield AI"
        for phone in phone_numbers:
            await self.send_sms_alert(phone, message)

notification_service = NotificationService()
