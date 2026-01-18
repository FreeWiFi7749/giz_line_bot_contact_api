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

## デプロイ

Railway にデプロイする場合、以下の環境変数を設定してください：

- `DATABASE_URL`: PostgreSQL 接続URL
- `AWS_REGION`: AWS リージョン
- `AWS_ACCESS_KEY_ID`: AWS アクセスキー
- `AWS_SECRET_ACCESS_KEY`: AWS シークレットキー
- `SES_FROM_EMAIL`: 送信元メールアドレス
- `ADMIN_EMAIL`: 運営通知先メールアドレス
- `LINE_CHANNEL_ID`: LINE チャネルID
- `LIFF_ORIGIN`: LIFF オリジン

### AWS SES 認証方式（2026年ベストプラクティス）

本APIは2つの認証方式をサポートしています：

**開発環境（IAM Access Key）:**
- `SES_ROLE_ARN` を設定しない
- `AWS_ACCESS_KEY_ID` と `AWS_SECRET_ACCESS_KEY` を直接使用

**本番環境（STS AssumeRole + キャッシング）:**
- `SES_ROLE_ARN` を設定すると自動的にSTSモードに切り替わる
- 一時認証情報を使用（1時間有効、5分前に自動更新）
- セキュリティ向上、CloudTrail追跡可能

**本番環境のセットアップ手順:**

1. IAM Role 作成: `SES-Railway-Role`
2. SES送信ポリシーをRoleにアタッチ
3. AssumeRole用ユーザー作成: `railway-sts-user`
4. AssumeRole権限をユーザーに付与
5. Railway環境変数に設定:
   - `AWS_ACCESS_KEY_ID`: railway-sts-user のアクセスキー
   - `AWS_SECRET_ACCESS_KEY`: railway-sts-user のシークレット
   - `SES_ROLE_ARN`: `arn:aws:iam::ACCOUNT_ID:role/SES-Railway-Role`
