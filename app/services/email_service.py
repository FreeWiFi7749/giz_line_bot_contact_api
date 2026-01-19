"""
Email service using Resend

Resend is a modern email API for developers.
https://resend.com/docs

無料枠: 3,000通/月
"""
import logging
from datetime import datetime

import resend

from ..config import settings
from ..schemas import InquiryCreate

logger = logging.getLogger(__name__)

CATEGORY_NAMES = {
    "general": "一般的なお問い合わせ",
    "support": "サポート",
    "bug": "不具合報告",
    "suggestion": "ご提案",
}


def init_resend():
    """Initialize Resend with API key"""
    if settings.RESEND_API_KEY:
        resend.api_key = settings.RESEND_API_KEY
        logger.info("Resend initialized")
    else:
        logger.warning("RESEND_API_KEY not set - email sending will fail")


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
    if not settings.RESEND_API_KEY:
        logger.error("RESEND_API_KEY not configured")
        return False
    
    init_resend()
    
    category_name = get_category_display_name(data.category)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    user_success = _send_user_confirmation_email(data, category_name)
    admin_success = _send_admin_notification_email(data, category_name, timestamp)
    
    return user_success and admin_success


def _send_user_confirmation_email(data: InquiryCreate, category_name: str) -> bool:
    """Send confirmation email to user"""
    user_html = f"""
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background-color: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h1 style="color: #333; margin-bottom: 20px; font-size: 24px;">お問い合わせを受け付けました</h1>
            <p style="color: #666; line-height: 1.6;">
                {data.name} 様
            </p>
            <p style="color: #666; line-height: 1.6;">
                お問い合わせありがとうございます。<br>
                以下の内容で受け付けました。<br>
                確認後、担当者よりご連絡いたします。
            </p>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #00B900;">
                <p style="margin: 8px 0; color: #333;"><strong>種別:</strong> {category_name}</p>
                <p style="margin: 8px 0; color: #333;"><strong>メールアドレス:</strong> {data.email}</p>
                <p style="margin: 8px 0; color: #333;"><strong>内容:</strong></p>
                <div style="background-color: #ffffff; padding: 15px; border-radius: 4px; margin-top: 10px;">
                    <pre style="white-space: pre-wrap; font-family: inherit; color: #333; margin: 0;">{data.message}</pre>
                </div>
            </div>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            
            <p style="color: #999; font-size: 12px; line-height: 1.5;">
                このメールは自動送信です。<br>
                心当たりがない場合は、このメールは破棄してください。
            </p>
        </div>
    </body>
    </html>
    """
    
    user_text = f"""{data.name} 様

お問い合わせありがとうございます。

▼お問い合わせ内容
種別: {category_name}
メールアドレス: {data.email}

{data.message}

このメールは自動送信です。"""
    
    try:
        resend.Emails.send({
            "from": settings.EMAIL_FROM,
            "to": [data.email],
            "subject": "【Gizmodo Japan LINE Bot】お問い合わせを受け付けました",
            "html": user_html,
        })
        logger.info(f"User confirmation email sent to {data.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send user confirmation email: {e}")
        return False


def _send_admin_notification_email(data: InquiryCreate, category_name: str, timestamp: str) -> bool:
    """Send notification email to admin"""
    admin_html = f"""
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background-color: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h1 style="color: #333; margin-bottom: 20px; font-size: 24px;">新しいお問い合わせ</h1>
            
            <div style="background-color: #e3f2fd; padding: 20px; border-left: 4px solid #2196f3; border-radius: 4px; margin: 20px 0;">
                <p style="margin: 8px 0; color: #333;"><strong>名前:</strong> {data.name}</p>
                <p style="margin: 8px 0; color: #333;"><strong>メール:</strong> <a href="mailto:{data.email}" style="color: #2196f3;">{data.email}</a></p>
                <p style="margin: 8px 0; color: #333;"><strong>種別:</strong> {category_name}</p>
                <p style="margin: 8px 0; color: #333;"><strong>送信日時:</strong> {timestamp}</p>
            </div>
            
            <p style="color: #333; font-weight: bold; margin-top: 25px;">内容:</p>
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 10px;">
                <pre style="white-space: pre-wrap; font-family: inherit; color: #333; margin: 0;">{data.message}</pre>
            </div>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            
            <p style="color: #666; font-size: 14px; line-height: 1.5;">
                このメールに返信すると、ユーザー ({data.email}) に直接届きます。
            </p>
        </div>
    </body>
    </html>
    """
    
    admin_text = f"""新しいお問い合わせがありました。

名前: {data.name}
メール: {data.email}
種別: {category_name}
送信日時: {timestamp}

▼内容
{data.message}

※このメールに返信するとユーザーに届きます。"""
    
    try:
        resend.Emails.send({
            "from": settings.EMAIL_FROM,
            "to": [settings.ADMIN_EMAIL],
            "reply_to": data.email,
            "subject": f"【LINE Bot お問い合わせ】{data.name} さんから新規問い合わせ",
            "html": admin_html,
        })
        logger.info(f"Admin notification email sent to {settings.ADMIN_EMAIL}")
        return True
    except Exception as e:
        logger.error(f"Failed to send admin notification email: {e}")
        return False
