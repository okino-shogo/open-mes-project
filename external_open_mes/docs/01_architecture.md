# システムアーキテクチャ概要

サーバーサイドは Python 言語と Djangoフレームワーク によって実装されており、WebインターフェースはDjangoのテンプレートを用いたHTML/JavaScriptで提供されます。GitHub上のソースコード比率を見ると、HTMLテンプレートが約55%、Pythonコードが約45%を占めており、バックエンドとフロントエンドの双方から構成されていることがわかります
([github.com](https://github.com/mihatama/open-mes-project))。アプリケーションはDockerコンテナ上で動作し、データベースには PostgreSQL を採用しています
([github.com](https://github.com/mihatama/open-mes-project))。システム全体はクライアント-サーバ構成になっており、クライアント（ブラウザ）からのリクエストをDjangoベースのWebサーバが処理し、必要に応じてPostgreSQLデータベースにアクセスします。

このプロジェクトではマイクロサービスではなく、DjangoによるモノリシックなWebアプリケーション構造を採っています。ただし内部はドメインごとに複数のモジュール（Djangoアプリ）に分割されており、機能単位で管理しやすいよう工夫されています（詳細は後述の[コード構成](./07_developer_guide/01_codebase_structure.md)を参照）。コンテナ構成としては、少なくとも以下のサービスがDocker Composeで定義されます：

- Webアプリケーションコンテナ（サービス名: open_mes）：Djangoアプリを実行。Pythonランタイムとアプリケーションコードを含み、内部でDjangoの開発サーバまたはGunicornなどのWSGIサーバが動作します。
- データベースコンテナ（サービス名: postgres）：PostgreSQLデータベース。アプリコンテナから接続され、アプリケーションデータを永続化します。

上記2コンテナ間はDocker Composeネットワークで連携し、データベースホスト名はpostgresとしてアプリから参照されます（.envで設定
[github.com](https://github.com/mihatama/open-mes-project/blob/main/README.md?plain=1#L103-L112)）。なお、開発者は必要に応じてローカル環境でアプリケーションを直接実行することも可能ですが、基本的にはDocker上での動作を前提としています。