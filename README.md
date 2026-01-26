# Gizmodo Japan LINE Bot Contact API

LINE Bot お問い合わせフォーム用バックエンドAPI。LINE LIFF からのお問い合わせを受け付け、データベースに保存し、確認メールを送信します。

## 主な機能

- LINE LIFF からのお問い合わせフォーム送信を受け付け
- LINE IDトークン検証によるユーザー認証
- Cloudflare Turnstile によるボット対策（人間確認）
- PostgreSQL へのお問い合わせ保存（非同期）
- Resend API によるメール送信
  - ユーザー宛確認メール（HTML/テキスト両対応）
  - 運営宛通知メール

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| フレームワーク | FastAPI |
| 言語 | Python 3.11+ |
| データベース | PostgreSQL（asyncpg） |
| ORM | SQLAlchemy 2.0（非同期対応） |
| メール送信 | Resend API |
| 認証 | python-jose（LINE IDトークン検証） |
| バリデーション | Pydantic 2 |
| デプロイ | Railway |

## API エンドポイント

### POST /api/inquiry

お問い合わせを送信します。

**リクエストボディ:**
```json
{
  "name": "お名前",
  "email": "email@example.com",
  "category": "general",
  "message": "お問い合わせ内容",
  "idToken": "LINE_ID_TOKEN（オプション）",
  "turnstileToken": "TURNSTILE_TOKEN（オプション）"
}
```

**カテゴリ:**
| 値 | 説明 |
|----|------|
| `general` | 一般的なお問い合わせ |
| `support` | サポート |
| `bug` | 不具合報告 |
| `suggestion` | ご提案 |

**レスポンス:**
```json
{
  "ok": true,
  "message": "お問い合わせを受け付けました。確認メールをお送りしました。"
}
```

### GET /health

ヘルスチェックエンドポイント。

**レスポンス:**
```json
{
  "status": "ok"
}
```

### GET /

ルートエンドポイント。APIの基本情報を返します。

## プロジェクト構造

```
giz_line_bot_contact_api/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI アプリケーション
│   ├── config.py         # 設定管理
│   ├── database.py       # データベース接続
│   ├── models.py         # SQLAlchemy モデル
│   ├── schemas.py        # Pydantic スキーマ
│   └── services/         # ビジネスロジック
│       ├── __init__.py
│       ├── email_service.py   # Resend メール送信
│       ├── line_auth.py       # LINE IDトークン検証
│       └── turnstile.py       # Cloudflare Turnstile 検証
├── pyproject.toml        # Poetry 依存関係
├── poetry.lock
└── railway.toml          # Railway デプロイ設定
```

## セットアップ

### 1. 依存関係のインストール

```bash
poetry install
```

### 2. 環境変数の設定

```bash
cp .env.example .env
```

`.env` ファイルを編集し、以下の必須項目を設定してください。

| 環境変数 | 説明 |
|---------|------|
| `DATABASE_URL` | PostgreSQL 接続URL（asyncpg形式） |
| `RESEND_API_KEY` | Resend API キー |
| `EMAIL_FROM` | 送信元メールアドレス |
| `ADMIN_EMAIL` | 管理者通知先メールアドレス |
| `LINE_CHANNEL_ID` | LINE チャネルID |
| `LIFF_ORIGIN` | LIFF オリジン（通常 `https://liff.line.me`） |
| `ALLOWED_ORIGINS` | CORS許可オリジン |

オプション:
| 環境変数 | 説明 |
|---------|------|
| `TURNSTILE_SECRET_KEY` | Cloudflare Turnstile シークレットキー |

### 3. 開発サーバーの起動

```bash
poetry run uvicorn app.main:app --reload --port 8000
```

開発サーバーが `http://localhost:8000` で起動します。

API ドキュメントは `http://localhost:8000/docs` で確認できます。

## デプロイ（Railway）

1. Railway プロジェクトを作成
2. GitHub リポジトリを接続
3. 環境変数を設定
4. PostgreSQL アドオンを追加
5. デプロイ

`railway.toml` に必要な設定が含まれています。

## メール送信について

このAPIは [Resend](https://resend.com/) を使用してメールを送信します。

- 無料枠: 3,000通/月
- HTML/テキスト両形式でメール送信
- ユーザーへの確認メールと管理者への通知メールを同時送信
- XSS対策としてユーザー入力をエスケープ処理

## 関連リポジトリ

| リポジトリ | 説明 |
|-----------|------|
| [giz_line_bot_contact_liff_web](https://github.com/FreeWiFi7749/giz_line_bot_contact_liff_web) | お問い合わせフォーム LIFF（Next.js + Railway） |
| [giz_line_bot](https://github.com/frwi-tech/giz_line_bot) | LINE Bot バックエンド（FastAPI + Railway） |
| [giz_line_analytics_web](https://github.com/FreeWiFi7749/giz_line_analytics_web) | LINE Analytics ダッシュボード（Qwik + Cloudflare Pages） |
| [giz_line_delivery_app](https://github.com/FreeWiFi7749/giz_line_delivery_app) | 手動配信アプリ（Qwik + Cloudflare Pages） |

## ライセンス

MIT
