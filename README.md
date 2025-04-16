# open-mes-project

## 動作推奨環境

**推奨OS:** Ubuntu

**推奨環境:**

1.  **Ubuntu Server 24.04 LTS (最新版):** 本番環境での運用に最適です。安定性とセキュリティに優れており、サーバー用途に特化した機能が充実しています。
2.  **Ubuntu Desktop 24.04 LTS (最新版):** 開発環境やテスト環境として利用できます。デスクトップ環境が必要な場合に適しています。

**必須ソフトウェア:**

*   **Docker:** コンテナ化された環境でアプリケーションを実行するために必要です。
*   **Docker Compose:** 複数のDockerコンテナを定義し、管理するためのツールです。
*   **PostgreSQL:** データベースとして使用します。

**備考:** 上記以外のOSでも動作する可能性がありますが、検証は行っておりません。

## 開発環境の構築
venvで使用するライブラリを入れることをおすすめします。
使用するコマンド
```

sudo apt update
sudo apt install libpq-dev


# venvが入っていない場合
sudo apt install python3-venv

# 仮想環境に入る
source venv/bin/activate

# ライブラリインストール
pip install -r ./open_mes/image/requirements.txt

```

## 初回は下記コマンドを実行
```
docker compose exec -it open_mes python3 manage.py makemigrations base
docker compose exec -it open_mes python3 manage.py makemigrations inventory
docker compose exec -it open_mes python3 manage.py makemigrations machine
docker compose exec -it open_mes python3 manage.py makemigrations master
docker compose exec -it open_mes python3 manage.py makemigrations production
docker compose exec -it open_mes python3 manage.py makemigrations quality
docker compose exec -it open_mes python3 manage.py makemigrations users
docker compose exec -it open_mes python3 manage.py migrate
```
## 管理者を登録
```
docker compose exec -it open_mes python3 manage.py createsuperuser
```

## .envファイルのサンプル

下記コマンドでセキュリティキーを再発行する
```
docker compose exec -it open_mes python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
.env
```
SECRET_KEY=(生成したセキュリティキーをここに記載する)

DEBUG=True

ALLOWED_HOSTS=*
CSRF_TRUSTED_ORIGINS=*

DB_ENGINE=django.db.backends.postgresql
DB_NAME=open_mes
DB_USER=django
DB_PASSWORD=django
DB_HOST=postgres
DB_PORT=5432

```