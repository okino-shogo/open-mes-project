# open-mes-project

## 初回は下記コマンドを実行
docker compose exec -it open_mes python3 manage.py makemigrations
docker compose exec -it open_mes python3 manage.py migrate

## 管理者を登録
docker compose exec -it open_mes python3 manage.py createsuperuser
