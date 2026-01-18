# Gizmodo Japan LINE Bot Contact API

LINE Bot お問い合わせフォーム用バックエンドAPI

## 機能

- LINE LIFF からのお問い合わせフォーム送信を受け付け
- LINE IDトークン検証によるユーザー認証
- PostgreSQL へのお問い合わせ保存
- AWS SES によるメール送信
  - ユーザー宛確認メール
  - 運営宛通知メール（Reply-To でユーザーに直接返信可能）

## API エンドポイント

### POST /api/inquiry

お問い合わせを送信

**リクエストボディ:**
```json
{
  "name": "お名前",
  "email": "email@example.com",
  "category": "general",
  "message": "お問い合わせ内容",
  "idToken": "LINE_ID_TOKEN"
}
```

**カテゴリ:**
- `general`: 一般的なお問い合わせ
- `support`: サポート
- `bug`: 不具合報告
- `suggestion`: ご提案

### GET /health

ヘルスチェック

## 環境変数

`.env.example` を参照してください。

## ローカル開発

```bash
# 依存関係インストール
poetry install

# 開発サーバー起動
poetry run uvicorn app.main:app --reload --port 8000
```

## デプロイ（Railway）

### AWS SES 認証設定（2026年ベストプラクティス）

本番環境では **STS AssumeRole** を使用します。一時認証情報による高セキュリティな認証方式です。

#### 必要な AWS リソース

1. **IAM Role**: `SES-Railway-Role`
   - ポリシー: `AmazonSESFullAccess`（または `ses:SendEmail`, `ses:SendRawEmail` 権限）
   - 信頼関係: AssumeRole 用ユーザーからのアクセスを許可

2. **IAM User**: `railway-sts-user`
   - ポリシー: `sts:AssumeRole` 権限（上記 Role に対して）
   - アクセスキー: Railway 環境変数に設定

#### Railway 環境変数

```
DATABASE_URL=postgresql+asyncpg://...
AWS_REGION=us-east-2
AWS_ACCESS_KEY_ID=<railway-sts-user のアクセスキー>
AWS_SECRET_ACCESS_KEY=<railway-sts-user のシークレット>
SES_ROLE_ARN=arn:aws:iam::<ACCOUNT_ID>:role/SES-Railway-Role
SES_FROM_EMAIL=no-reply@gizmodojp-line-bot.frwi.tech
ADMIN_EMAIL=admin@example.com
LINE_CHANNEL_ID=<LINE チャネルID>
LIFF_ORIGIN=https://liff.line.me
ALLOWED_ORIGINS=https://liff.line.me
```

#### 認証の仕組み

- `SES_ROLE_ARN` が設定されている場合、STS AssumeRole で一時認証情報を取得
- 認証情報は1時間有効、有効期限5分前に自動更新（キャッシング）
- CloudTrail で全ての SES 送信を追跡可能

#### 開発環境（オプション）

`SES_ROLE_ARN` を空または未設定にすると、`AWS_ACCESS_KEY_ID` と `AWS_SECRET_ACCESS_KEY` を直接使用する IAM Access Key モードで動作します。
