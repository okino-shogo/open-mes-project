# open-mes-project

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