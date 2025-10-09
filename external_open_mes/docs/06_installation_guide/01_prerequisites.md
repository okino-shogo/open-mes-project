# 開発・実行環境の前提条件

本章では、open-mes-projectを開発・実行する環境の構築方法や、初期設定・起動手順、さらには利用中につまずきやすい点への対処方法について解説します。

## 対応OS
本システムはLinux環境での動作を想定しています。特に Ubuntu 24.04 LTS 系での利用が推奨されており、サーバ用途にはUbuntu Server 24.04、開発用途にはUbuntu Desktop 24.04が適しています
([github.com](https://github.com/mihatama/open-mes-project/blob/main/README.md?plain=1#L46-L50))。他のOS（例えばWindowsやmacOS）でもDockerを介して動作する可能性はありますが、公式には検証されていません
([github.com](https://github.com/mihatama/open-mes-project/blob/main/README.md?plain=1#L46-L50))。Windowsユーザーの場合はWSL2上でUbuntuを動かすか、またはLinuxサーバを利用すると良いでしょう。

## 必要ソフトウェア
導入には以下のソフトウェアが必要です
([github.com](https://github.com/mihatama/open-mes-project/blob/main/README.md?plain=1#L52-L60))。

- **Docker**：アプリケーションをコンテナ環境で実行するために使用します
  ([github.com](https://github.com/mihatama/open-mes-project/blob/main/README.md?plain=1#L52-L60))。Docker Engineがインストールされ、`docker`コマンドが使える状態にしてください。
- **Docker Compose**：複数のコンテナ（アプリケーションコンテナとDBコンテナ）を一括管理するために使用します
  (github.com)。Docker Desktop同梱のComposeまたは`docker compose`プラグインが利用可能であることを確認してください。
- **PostgreSQL**：データベースそのものはDocker上で動かしますが、ホスト側でPostgreSQLクライアントツールなどを使用する場合はインストールしておくと便利です
  (github.com)。必須ではありませんが、例えばデータベースの状態確認やバックアップ取得に`psql`クライアントが役立ちます。

## ハードウェア要件
小規模なデータであれば、メモリ2GB程度・CPUデュアルコアの環境でも動作可能ですが、Dockerを使うため多少のオーバーヘッドがあります。開発PCでは4GB以上のRAMを推奨します。ディスク容量はDockerイメージやデータ格納用に数GB程度必要です（データ量に応じて増加）。