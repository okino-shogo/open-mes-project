# セットアップ手順

以下では、Dockerを利用したセットアップ手順を中心に説明します。コマンドは基本的にLinuxシェル想定です。

## 1. コードの入手
GitHubのopen-mes-projectリポジトリからソースコードを取得します。gitが使える場合は以下のコマンドでクローンできます。
```bash
git clone https://github.com/mihatama/open-mes-project.git
```
あるいはGitHub上からZIPアーカイブをダウンロードして任意のディレクトリに展開してください。

## 2. 環境変数ファイルの設定
前述した `.env` ファイルをプロジェクトのルートディレクトリ（`open-mes-project/` 内）に作成します。READMEに記載のサンプルを参考に、`SECRET_KEY`やデータベース情報を正しく設定してください
(github.com
github.com)。特に、`SECRET_KEY`はDjangoのセキュリティ上重要なキーです。未設定の場合アプリケーションが起動しないため、必ず一意のランダム値を設定します（キー生成コマンドで取得可能
github.com)。デバッグ目的で開発中は`DEBUG=True`のままで構いませんが、本番環境にデプロイする際は`DEBUG=False`に変更し、`ALLOWED_HOSTS`に適切なドメインやIPを設定してください。

## 3. Dockerイメージのビルドとコンテナ起動
プロジェクトディレクトリに移動し、Docker Composeでサービスを起動します。
```bash
cd open-mes-project
docker compose up -d
```
初回はアプリケーション用Dockerイメージのビルドが行われます。Dockerfile内ではPythonランタイムのセットアップや必要ライブラリのインストール（`requirements.txt`経由
github.com）が自動実行されます。`docker compose up -d`コマンドにより、バックグラウンドで**open_mes（アプリケーション）コンテナとpostgres（データベース）**コンテナの2つが起動します。コンテナの状態は`docker compose ps`で確認できます。どちらもStateが`running`になっていればOKです。

**補足:** 開発用途でDockerを使わず直接ホストOS上で実行したい場合は、システムにPythonとPostgreSQLを直接セットアップする必要があります。その際は、まず`sudo apt install libpq-dev`でPostgreSQLのクライアントライブラリを導入し、`python3 -m venv venv`で仮想環境を作成・有効化してから、`pip install -r open_mes/image/requirements.txt`を実行します
(github.com
github.com)。さらにPostgreSQLをローカルに用意し、`.env`の`DB_HOST`を`localhost`に変えるなどの調整が必要です。基本的にはDocker利用を推奨します。

## 4. データベースのマイグレーション
コンテナ起動後、Djangoのモデルに対応するテーブルをデータベースに作成します。以下のマイグレーションコマンドを順に実行してください（※Dockerコンテナ内でコマンドを実行します）
(github.com)。

```bash
docker compose exec -it open_mes python3 manage.py makemigrations base
docker compose exec -it open_mes python3 manage.py makemigrations inventory
docker compose exec -it open_mes python3 manage.py makemigrations machine
docker compose exec -it open_mes python3 manage.py makemigrations master
docker compose exec -it open_mes python3 manage.py makemigrations production
docker compose exec -it open_mes python3 manage.py makemigrations quality
docker compose exec -it open_mes python3 manage.py makemigrations users
docker compose exec -it open_mes python3 manage.py migrate
```
上記により、各アプリケーション（base, inventory, machine, master, production, quality, users）のマイグレーションファイルが適用され、テーブル作成やスキーマ変更が行われます
(github.com)。`migrate`コマンドまで正常に完了したら、データベース準備は完了です。エラーが出る場合は`.env`のDB設定誤りやPostgreSQLコンテナの起動失敗が考えられますので、設定を見直してください。

## 5. 管理者ユーザーの作成
アプリケーションにログインし管理操作を行うため、スーパーユーザー（管理者）のアカウントを作成します。以下のコマンドで対話的にユーザー名・メールアドレス・パスワードを設定してください
(github.com)。

```bash
docker compose exec -it open_mes python3 manage.py createsuperuser
```
このユーザーはシステム内で最高権限を持ち、各種マスタ登録や他ユーザー管理、設定変更が可能になります。メールアドレスはダミーでも構いませんが、ユーザー名とパスワードは忘れないよう控えておきます（パスワードは入力しても画面に表示されません）。

## 6. アプリケーションへのアクセス
以上で初期セットアップは完了です。ブラウザを開き、アプリケーションにアクセスしてみましょう。デフォルトではコンテナ内のDjango開発サーバがポート8000で起動しているため、ホストの`http://localhost:8000/` にアクセスします。ログイン画面が表示されたら、先ほど作成した管理者ユーザーの資格情報でログインしてください。無事ログインできればセットアップ成功です。初期画面としてはダッシュボードやメニュー画面が表示され、各機能（在庫管理・生産管理等）へ遷移できるようになっているはずです。

**メモ:** Docker Composeの設定によってはポートをホストに公開していない場合があります。その際は`docker compose logs -f open_mes`でログを確認し、「Starting development server at http://0.0.0.0:8000」等のメッセージを探してください。もし見当たらない場合、Dockerfile/ComposeでデフォルトのCMDが実行されていない可能性があります。必要に応じて`docker compose exec -it open_mes python3 manage.py runserver 0.0.0.0:8000`で開発サーバを手動起動してポートフォワードを確認してください。