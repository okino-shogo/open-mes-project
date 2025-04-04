# open-mes-project

## 初回は下記コマンドを実行

docker compose exec -it open_mes python3 manage.py makemigrations base
docker compose exec -it open_mes python3 manage.py makemigrations inventory
docker compose exec -it open_mes python3 manage.py makemigrations machine
docker compose exec -it open_mes python3 manage.py makemigrations master
docker compose exec -it open_mes python3 manage.py makemigrations production
docker compose exec -it open_mes python3 manage.py makemigrations quality
docker compose exec -it open_mes python3 manage.py makemigrations users
docker compose exec -it open_mes python3 manage.py migrate

## 管理者を登録
docker compose exec -it open_mes python3 manage.py createsuperuser
