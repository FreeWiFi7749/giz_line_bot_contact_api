"""
Email service using AWS SES

認証方式:
- SES_ROLE_ARN が設定されている場合: STS AssumeRole + キャッシング（本番向け）
- SES_ROLE_ARN が未設定の場合: IAM Access Key（開発向け）
"""
import logging
from datetime import datetime, timedelta, timezone

import boto3
from botocore.exceptions import ClientError

from ..config import settings
from ..schemas import InquiryCreate

logger = logging.getLogger(__name__)

# Category display names
CATEGORY_NAMES = {
    "general": "一般的なお問い合わせ",
    "support": "サポート",
    "bug": "不具合報告",
    "suggestion": "ご提案",
}


class SESCredentialManager:
    """
    AWS SES 認証情報マネージャー
    
    STS AssumeRole を使用して一時認証情報を取得し、キャッシュする。
    認証情報は有効期限の5分前に自動更新される。
    
    SES_ROLE_ARN が未設定の場合は、直接 IAM Access Key を使用する。
    """
    
    def __init__(self):
        self.credentials = None
        self.expiration = None
        self._sts_client = None
        self._use_sts = bool(settings.SES_ROLE_ARN)
        
        if self._use_sts:
            logger.info("SES認証: STS AssumeRole モード（本番向け）")
        else:
            logger.info("SES認証: IAM Access Key モード（開発向け）")
    
    def _get_sts_client(self):
        """STS クライアントを取得（遅延初期化）"""
        if self._sts_client is None:
            self._sts_client = boto3.client(
                "sts",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
        return self._sts_client
    
    def get_ses_client(self):
        """
        キャッシュされた認証情報で SES クライアントを返す
        
        STS モードの場合:
        - キャッシュが有効なら再利用
        - 有効期限の5分前に自動更新
        
        IAM Access Key モードの場合:
        - 直接認証情報を使用
        """
        if not self._use_sts:
            return self._create_direct_ses_client()
        
        now = datetime.now(timezone.utc)
        
        if self.credentials and self.expiration:
            expiration_aware = self.expiration
            if expiration_aware.tzinfo is None:
                expiration_aware = expiration_aware.replace(tzinfo=timezone.utc)
            
            if expiration_aware > now + timedelta(minutes=5):
                return self._create_ses_client_from_credentials(self.credentials)
        
        self._refresh_credentials()
        return self._create_ses_client_from_credentials(self.credentials)
    
    def _refresh_credentials(self):
        """AssumeRole で新しい認証情報を取得"""
        try:
            sts_client = self._get_sts_client()
            response = sts_client.assume_role(
                RoleArn=settings.SES_ROLE_ARN,
                RoleSessionName="railway-ses-session",
                DurationSeconds=3600,
            )
            self.credentials = response["Credentials"]
            self.expiration = response["Credentials"]["Expiration"]
            logger.info(f"SES認証情報を更新: 有効期限 {self.expiration}")
        except ClientError as e:
            logger.error(f"AssumeRole エラー: {e}")
            raise
    
    def _create_direct_ses_client(self):
        """IAM Access Key で直接 SES クライアントを生成"""
        return boto3.client(
            "ses",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
    
    def _create_ses_client_from_credentials(self, credentials):
        """一時認証情報で SES クライアントを生成"""
        return boto3.client(
            "ses",
            region_name=settings.AWS_REGION,
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
        )


# グローバルインスタンス（シングルトン）
_credential_manager = None


def get_credential_manager() -> SESCredentialManager:
    """SES 認証情報マネージャーを取得"""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = SESCredentialManager()
    return _credential_manager


def get_ses_client():
    """Get AWS SES client（認証方式を自動選択）"""
    return get_credential_manager().get_ses_client()


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
    ses = get_ses_client()
    category_name = get_category_display_name(data.category)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    user_success = _send_user_confirmation_email(ses, data, category_name)
    admin_success = _send_admin_notification_email(ses, data, category_name, timestamp)
    
    return user_success and admin_success


def _send_user_confirmation_email(ses, data: InquiryCreate, category_name: str) -> bool:
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
        ses.send_email(
            Source=settings.SES_FROM_EMAIL,
            Destination={"ToAddresses": [data.email]},
            Message={
                "Subject": {
                    "Data": "【Gizmodo Japan LINE Bot】お問い合わせを受け付けました",
                    "Charset": "UTF-8",
                },
                "Body": {
                    "Text": {"Data": user_text, "Charset": "UTF-8"},
                    "Html": {"Data": user_html, "Charset": "UTF-8"},
                },
            },
        )
        logger.info(f"User confirmation email sent to {data.email}")
        return True
    except ClientError as e:
        logger.error(f"Failed to send user confirmation email: {e}")
        return False


def _send_admin_notification_email(ses, data: InquiryCreate, category_name: str, timestamp: str) -> bool:
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
        ses.send_email(
            Source=settings.SES_FROM_EMAIL,
            Destination={"ToAddresses": [settings.ADMIN_EMAIL]},
            ReplyToAddresses=[data.email],
            Message={
                "Subject": {
                    "Data": f"【LINE Bot お問い合わせ】{data.name} さんから新規問い合わせ",
                    "Charset": "UTF-8",
                },
                "Body": {
                    "Text": {"Data": admin_text, "Charset": "UTF-8"},
                    "Html": {"Data": admin_html, "Charset": "UTF-8"},
                },
            },
        )
        logger.info(f"Admin notification email sent to {settings.ADMIN_EMAIL}")
        return True
    except ClientError as e:
        logger.error(f"Failed to send admin notification email: {e}")
        return False
