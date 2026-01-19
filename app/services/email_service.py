"""
Email service using Resend

Resend is a modern email API for developers.
https://resend.com/docs

無料枠: 3,000通/月
"""
import html
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import resend

from ..config import settings
from ..schemas import InquiryCreate

logger = logging.getLogger(__name__)

# Lazy initialization flag
_resend_initialized = False

# Japan Standard Time
JST = ZoneInfo("Asia/Tokyo")

CATEGORY_NAMES = {
    "general": "一般的なお問い合わせ",
    "support": "サポート",
    "bug": "不具合報告",
    "suggestion": "ご提案",
}


def _ensure_resend_initialized() -> bool:
    """
    Ensure Resend is initialized (lazy initialization pattern).
    Only initializes once per application lifetime.
    
    Returns:
        True if initialized successfully, False otherwise
    """
    global _resend_initialized
    
    if _resend_initialized:
        return True
    
    # Validate all required settings early
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set - email sending will fail")
        return False
    if not settings.EMAIL_FROM:
        logger.warning("EMAIL_FROM not set - email sending will fail")
        return False
    if not settings.ADMIN_EMAIL:
        logger.warning("ADMIN_EMAIL not set - admin notification will fail")
        return False
    
    resend.api_key = settings.RESEND_API_KEY
    _resend_initialized = True
    logger.info("Resend initialized")
    return True


def get_category_display_name(category: str) -> str:
    """Get display name for category"""
    return CATEGORY_NAMES.get(category, category)


def send_inquiry_emails(data: InquiryCreate) -> bool:
    """
    Send confirmation email to user and notification email to admin
    
    Args:
        data: Inquiry data
        
    Returns:
        True if both emails sent successfully, False otherwise
    """
    if not _ensure_resend_initialized():
        logger.error("RESEND_API_KEY not configured")
        return False
    
    category_name = get_category_display_name(data.category)
    # Use timezone-aware datetime in JST
    timestamp = datetime.now(tz=JST).strftime("%Y-%m-%d %H:%M:%S")
    
    user_success = _send_user_confirmation_email(data, category_name)
    admin_success = _send_admin_notification_email(data, category_name, timestamp)
    
    return user_success and admin_success


def _send_user_confirmation_email(data: InquiryCreate, category_name: str) -> bool:
    """Send confirmation email to user"""
    # Escape user input to prevent XSS/HTML injection
    safe_name = html.escape(data.name)
    safe_email = html.escape(data.email)
    safe_message = html.escape(data.message)
    safe_category = html.escape(category_name)
    
    user_html = f"""
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background-color: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h1 style="color: #333; margin-bottom: 20px; font-size: 24px;">お問い合わせを受け付けました</h1>
            <p style="color: #666; line-height: 1.6;">
                {safe_name} 様
            </p>
            <p style="color: #666; line-height: 1.6;">
                お問い合わせありがとうございます。<br>
                以下の内容で受け付けました。<br>
                確認後、担当者よりご連絡いたします。
            </p>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #00B900;">
                <p style="margin: 8px 0; color: #333;"><strong>種別:</strong> {safe_category}</p>
                <p style="margin: 8px 0; color: #333;"><strong>メールアドレス:</strong> {safe_email}</p>
                <p style="margin: 8px 0; color: #333;"><strong>内容:</strong></p>
                <div style="background-color: #ffffff; padding: 15px; border-radius: 4px; margin-top: 10px;">
                    <pre style="white-space: pre-wrap; font-family: inherit; color: #333; margin: 0;">{safe_message}</pre>
                </div>
            </div>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            
            <p style="color: #999; font-size: 12px; line-height: 1.5;">
                このメールは自動送信です。<br>
                追加のご質問がある場合は、このメールに返信してください。<br>
                心当たりがない場合は、このメールは破棄してください。
            </p>
        </div>
    </body>
    </html>
    """
    
    user_text = f"""{safe_name} 様

お問い合わせありがとうございます。

▼お問い合わせ内容
種別: {safe_category}
メールアドレス: {safe_email}

{safe_message}

このメールは自動送信です。
追加のご質問がある場合は、このメールに返信してください。"""
    
    try:
        resp = resend.Emails.send({
            "from": settings.EMAIL_FROM,
            "to": [data.email],
            "reply_to": settings.ADMIN_EMAIL,
            "subject": "【Gizmodo Japan LINE Bot】お問い合わせを受け付けました",
            "html": user_html,
            "text": user_text,
        })
        email_id = resp.get("id") if isinstance(resp, dict) else getattr(resp, "id", "unknown")
        logger.info("User confirmation email sent to %s (id: %s)", data.email, email_id)
        return True
    except Exception:
        logger.exception("Failed to send user confirmation email")
        return False


def _send_admin_notification_email(data: InquiryCreate, category_name: str, timestamp: str) -> bool:
    """Send notification email to admin"""
    # Escape user input to prevent XSS/HTML injection
    safe_name = html.escape(data.name)
    safe_email = html.escape(data.email)
    safe_message = html.escape(data.message)
    safe_category = html.escape(category_name)
    safe_timestamp = html.escape(timestamp)
    
    admin_html = f"""
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background-color: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h1 style="color: #333; margin-bottom: 20px; font-size: 24px;">新しいお問い合わせ</h1>
            
            <div style="background-color: #e3f2fd; padding: 20px; border-left: 4px solid #2196f3; border-radius: 4px; margin: 20px 0;">
                <p style="margin: 8px 0; color: #333;"><strong>名前:</strong> {safe_name}</p>
                <p style="margin: 8px 0; color: #333;"><strong>メール:</strong> <a href="mailto:{safe_email}" style="color: #2196f3;">{safe_email}</a></p>
                <p style="margin: 8px 0; color: #333;"><strong>種別:</strong> {safe_category}</p>
                <p style="margin: 8px 0; color: #333;"><strong>送信日時:</strong> {safe_timestamp}</p>
            </div>
            
            <p style="color: #333; font-weight: bold; margin-top: 25px;">内容:</p>
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 10px;">
                <pre style="white-space: pre-wrap; font-family: inherit; color: #333; margin: 0;">{safe_message}</pre>
            </div>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            
            <p style="color: #666; font-size: 14px; line-height: 1.5;">
                ※このメールは通知専用です。ユーザーに返信する場合は、上記メールアドレス宛に新規メールを作成してください。
            </p>
        </div>
    </body>
    </html>
    """
    
    admin_text = f"""新しいお問い合わせがありました。

名前: {safe_name}
メール: {safe_email}
種別: {safe_category}
送信日時: {safe_timestamp}

▼内容
{safe_message}

※このメールは通知専用です。ユーザーに返信する場合は、上記メールアドレス宛に新規メールを作成してください。"""
    
    try:
        resp = resend.Emails.send({
            "from": settings.EMAIL_FROM,
            "to": [settings.ADMIN_EMAIL],
            "subject": f"【LINE Bot お問い合わせ】{safe_name} さんから新規問い合わせ",
            "html": admin_html,
            "text": admin_text,
        })
        email_id = resp.get("id") if isinstance(resp, dict) else getattr(resp, "id", "unknown")
        logger.info("Admin notification email sent to %s (id: %s)", settings.ADMIN_EMAIL, email_id)
        return True
    except Exception:
        logger.exception("Failed to send admin notification email")
        return False
