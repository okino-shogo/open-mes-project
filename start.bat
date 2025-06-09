@echo off
REM ### Encoding and Unicode settings ###
REM 重要: このバッチファイル自体を「Shift_JIS (SJIS)」エンコーディングで保存してください。
REM SJIS環境で実行する場合、コンソールのコードページはデフォルト (932) のままとします。

setlocal EnableDelayedExpansion
REM スクリプトのあるディレクトリをカレントディレクトリにする
pushd "%~dp0"
REM --- Configuration ---
REM PROJECT_DIR は pushd によりカレントディレクトリがプロジェクトルートになるため、ここでのパス定義には不要
set "VENV_DIR=venv"
set "SCR_DIR=open_mes\scr"
set "IMAGE_DIR=open_mes\image"
set "REQUIREMENTS_FILE=requirements.txt"
set "MANAGE_PY=%SCR_DIR%\manage.py"
set "ENV_FILE=%SCR_DIR%\.env"
set "ENV_EXAMPLE_FILE=%SCR_DIR%\.env.example"
set "SETUP_COMPLETE_FLAG_FILE=%VENV_DIR%\.setup_complete"

REM --- Title ---
title Open MES Project Windows セットアップ

echo =======================================================
echo  Open MES Project Windows 開発環境セットアップ
echo =======================================================
echo(

REM --- Check if setup has been completed ---
if exist "%SETUP_COMPLETE_FLAG_FILE%" (
    echo [+] セットアップは以前に完了しています。
    echo [+] アプリケーションの起動に進みます...
    echo.
    goto :run_application
)

REM --- Initial Setup Process ---
echo このスクリプトは、Windows でプロジェクトを実行するためのセットアップを支援します。
echo プロジェクトのルートディレクトリから実行されることを前提としています。
echo(
echo [+] 初期セットアップを開始します...
echo(

REM --- Check for Python and Pip ---
echo [+] Python と Pip を確認しています...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] エラー: Python がインストールされていないか、システムの PATH に見つかりません。
    echo     Python 3.11 ^(https://www.python.org/^ から^) をインストールしてください。
    echo     インストール中に PATH に追加されていることを確認してください。
    goto :eof_final
)

pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] エラー: Pip がインストールされていません。Python が正しくインストールされていれば、これは通常発生しません。
    echo     Python のインストールに Pip が含まれていることを確認してください。
    goto :eof_final
)
echo     Python と Pip が見つかりました。
echo(

REM --- Create and Activate Virtual Environment ---
REM Create Virtual Environment
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [+] 仮想環境を "%VENV_DIR%" に作成しています...
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo [!] エラー: 仮想環境の作成に失敗しました。
        goto :eof_final
    )
    echo     仮想環境が正常に作成されました。
) else (
    echo [+] 仮想環境は "%VENV_DIR%" に既に存在します。
)
echo(
echo [+] セットアップのために仮想環境をアクティベートしています...
call "%VENV_DIR%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo [!] エラー: 仮想環境のアクティベートに失敗しました。
    goto :eof_final
)
echo     仮想環境がアクティベートされました。
echo(

REM --- Install Dependencies (during initial setup) ---
echo [+] 依存関係ファイル "%REQUIREMENTS_FILE%" の存在を確認しています...
if not exist "%REQUIREMENTS_FILE%" (
    echo [!] エラー: 依存関係ファイルが見つかりません: "%REQUIREMENTS_FILE%"
    echo     プロジェクトの "%IMAGE_DIR%" フォルダ内に "requirements.txt" が正しい名前で存在するか確認してください。
    echo     現在のスクリプトの場所 ^(カレントディレクトリ^): "%CD%"
    goto :deactivate_venv_after_setup_error
)
echo     依存関係ファイルが見つかりました。
echo [+] "%REQUIREMENTS_FILE%" から依存関係をインストールしています...
python -m pip install -r "%REQUIREMENTS_FILE%"
if %errorlevel% neq 0 (
    echo [!] エラー: 依存関係のインストールに失敗しました。上記のエラーメッセージを確認してください。
    echo     注意: このプロジェクトはデフォルトで SQLite を使用するように設定されています。
    echo     %REQUIREMENTS_FILE% に従って、PostgreSQL用の依存関係 'psycopg2' もインストールされます。
    echo     'psycopg2' に関連するエラーの場合:
    echo     1. PostgreSQL クライアントライブラリがインストールされ、PATH に含まれていることを確認してください。
    echo        主に SQLite を使用する予定でも、'psycopg2' が依存関係として含まれているため必要です。
    echo     2. Microsoft Visual C++ Build Tools が必要になる場合があります。
    echo     3. 'psycopg2' のインストールを容易にするために、手動で編集することを検討できます
    echo        "%REQUIREMENTS_FILE%" の 'psycopg2' を 'psycopg2-binary' に変更し、
    echo        その後、このスクリプトを再実行するか、手動で 'pip install -r "%REQUIREMENTS_FILE%"' を実行してください。
    echo     初期セットアップには、'psycopg2' を含むすべての依存関係の正常なインストールが必要です。
    goto :deactivate_venv_after_setup_error
) else (
    echo     依存関係が正常にインストールされました。^(オプションの PostgreSQL 使用のための 'psycopg2' を含みます^)
)
echo(

REM --- .env File Setup (during initial setup) ---
echo [+] %ENV_FILE% の .env ファイルを確認しています...
echo DEBUG: Point A - Just after echoing ENV_FILE check.
echo DEBUG: SCR_DIR is [%SCR_DIR%]
REM 書き込み先ディレクトリがなければ作成
if not exist "%SCR_DIR%" (
    echo DEBUG: Point B - SCR_DIR does not exist.
    echo [+] ディレクトリ "%SCR_DIR%" を作成しています...
    mkdir "%SCR_DIR%"
)
echo DEBUG: Point C - After SCR_DIR check/creation. ENV_FILE is [%ENV_FILE%]
REM Reset errorlevel before the next IF statement as a precaution
(call )
echo DEBUG: Point D - Before checking if ENV_FILE exists.

REM --- Check if .env file exists and branch accordingly ---
if exist "%ENV_FILE%" GOTO :handle_env_file_exists

REM --- .env file does NOT exist ---
    echo DEBUG: Point E - ENV_FILE does not exist. Starting .env creation block.
    REM This is the block for when .env does NOT exist
    echo [!] %ENV_FILE% が見つかりません。
    echo     デフォルトの .env ファイル ^(SQLite 用に設定済み^) が "%ENV_FILE%" に作成されます。
    echo     一意の SECRET_KEY が自動的に生成されます。
    echo     生成されたファイル内の他の設定を確認してください。
    echo(
    REM --- SECRET_KEY の生成 ---
    echo     新しい SECRET_KEY を生成しています...
    set "SECRET_KEY_TEMP_LINE_FILE=%TEMP%\secret_key_line.txt"
    set "SECRET_KEY_ERROR_FILE=%TEMP%\secret_key_error.txt"

    REM Python script now prints "SECRET_KEY=value" directly to the temp file
    "%VENV_DIR%\Scripts\python.exe" -c "from django.core.management.utils import get_random_secret_key; print(f'SECRET_KEY={get_random_secret_key()}')" > "%SECRET_KEY_TEMP_LINE_FILE%" 2> "%SECRET_KEY_ERROR_FILE%"
    set "PY_ERRORLEVEL=%errorlevel%"
    echo     デバッグ: Pythonコマンドのerrorlevel: %PY_ERRORLEVEL%

    if exist "%SECRET_KEY_ERROR_FILE%" (
        echo     デバッグ: Pythonエラー出力ファイル "%SECRET_KEY_ERROR_FILE%" の内容:
        type "%SECRET_KEY_ERROR_FILE%"
        del "%SECRET_KEY_ERROR_FILE%"
    )

    set "line_not_empty="
    if %PY_ERRORLEVEL% equ 0 (
        if exist "%SECRET_KEY_TEMP_LINE_FILE%" (
            REM Read the entire line from the temp file
            for /F "usebackq tokens=*" %%A in ("%SECRET_KEY_TEMP_LINE_FILE%") do set "line_not_empty=%%A"
            
            if defined line_not_empty (
                echo     SECRET_KEY が正常に生成されました: "!line_not_empty!"
                REM Write the SECRET_KEY to .env file (overwrite)
                (echo !line_not_empty!) > "%ENV_FILE%"
                if %errorlevel% neq 0 (
                    echo [!] エラー: SECRET_KEY を "%ENV_FILE%" に書き込めませんでした。
                    goto :handle_secret_key_generation_failure_critical
                )
                REM SECRET_KEY has been written, proceed to append other settings
                goto :append_other_env_settings
            ) else (
                echo     デバッグ: Pythonは成功しましたが、出力ファイル "%SECRET_KEY_TEMP_LINE_FILE%" が空です。
                goto :handle_secret_key_generation_failure
            )
        ) else (
            echo     デバッグ: Pythonは成功しましたが、出力ファイル "%SECRET_KEY_TEMP_LINE_FILE%" が見つかりません。
            goto :handle_secret_key_generation_failure
        )
    ) else {
        echo     デバッグ: Pythonコマンドが失敗しました (errorlevel: %PY_ERRORLEVEL%)。
        goto :handle_secret_key_generation_failure
    }

:handle_secret_key_generation_failure
    echo [!] 警告: SECRET_KEY の自動生成に失敗しました。
    echo            プレースホルダーキーが使用されます。"%ENV_FILE%" で手動で変更する必要があります。
    (echo SECRET_KEY=your_very_secret_and_unique_django_key_here_please_change_me_manually_!!!) > "%ENV_FILE%"
    if %errorlevel% neq 0 (
        echo [!] エラー: プレースホルダー SECRET_KEY を "%ENV_FILE%" に書き込めませんでした。
        goto :handle_secret_key_generation_failure_critical
    )
    REM Placeholder SECRET_KEY has been written, proceed to append other settings
    goto :append_other_env_settings

:append_other_env_settings
    if exist "%SECRET_KEY_TEMP_LINE_FILE%" del "%SECRET_KEY_TEMP_LINE_FILE%"
    echo(
    REM Append other settings to .env file
    echo DEBUG=True >> "%ENV_FILE%"
    echo ALLOWED_HOSTS=* >> "%ENV_FILE%"
    echo CSRF_TRUSTED_ORIGINS=* >> "%ENV_FILE%"
    echo DATABASE_URL=sqlite:///db.sqlite3 >> "%ENV_FILE%"
    echo     デフォルトの .env ファイル ^(SQLite 用に設定済み^) が "%ENV_FILE%" に作成されました。
    echo(
    echo     デバッグ: .env ファイルの最終内容:
    type "%ENV_FILE%"
    echo(
    goto :env_file_creation_done

:handle_secret_key_generation_failure_critical
    echo [!] 重大エラー: .env ファイルに SECRET_KEY を書き込めませんでした。
    echo     スクリプトを続行できません。ディレクトリの書き込み権限などを確認してください。
    pause
    goto :deactivate_venv_after_setup_error

:env_file_creation_done
    echo     ========================= 重要: 対応が必要です =========================
    echo     1. 新しく作成された "%ENV_FILE%" を確認してください。一意の SECRET_KEY が
    echo        自動的に生成されました。生成に失敗した場合は、手動で設定する必要があります。
    echo     2. ALLOWED_HOSTS やデータベース設定など、他の設定を確認してください。    
    echo     3. デフォルトのデータベースは SQLite です ^("%ENV_FILE%" で事前設定済み^)。
    echo        SQLite データベースファイル ^(例: デフォルトの .env に従い db.sqlite3^) は、
    echo        存在しない場合、マイグレーション中に Django によって自動的に作成されます ^(DATABASE_URL の設定に基づきます^)。
    echo     4. 代わりに PostgreSQL を使用する場合は、"%ENV_FILE%" の DATABASE_URL を編集し、
    echo        PostgreSQL サーバーの接続文字列 ^(例: postgres://USER:PASSWORD@HOST:PORT/NAME^) を入力し、
    echo        サーバーが実行されていることを確認する必要があります。
    echo     ===========================================================================
    echo(
    pause    
    GOTO :after_env_file_handling

:handle_env_file_exists
    REM This is the block for when .env DOES exist
    echo DEBUG: Point F - ENV_FILE exists.
    echo     %ENV_FILE% が見つかりました。正しく設定されていることを確認してください。
    echo     SQLite ^(デフォルト^) の場合: DATABASE_URL=sqlite:///db.sqlite3 ^(または同様の SQLite パス^)
    echo     そして、一意の SECRET_KEY が設定されていることを確認してください。
    echo     PostgreSQL を使用する場合は、DATABASE_URL が正しく設定されていることを確認してください。
    GOTO :after_env_file_handling

:after_env_file_handling
echo(
REM --- Database Setup Reminder (during initial setup) ---
echo =====================================
echo  データベース設定
echo =====================================
echo このプロジェクトはデフォルトで SQLite を使用するように設定されています。
echo 1. "%ENV_FILE%" に一意の SECRET_KEY が設定されていることを確認してください。
echo 2. SQLite データベース (例: デフォルトの .env に従い 'db.sqlite3') は、
echo    存在しない場合、マイグレーション中に Django によって自動的に作成されます。
echo    DATABASE_URL が 'sqlite:///db.sqlite3' ^(または同様の SQLite パス^) として "%ENV_FILE%" に設定されていることを確認してください。
echo.
echo 代わりに PostgreSQL を使用することを選択した場合 ("%ENV_FILE%" を変更した場合):
echo 1. PostgreSQL サーバーがインストールされ、実行されていることを確認してください。
echo 2. 必要な権限を持つデータベースとユーザーを作成済みであることを確認してください。
echo 3. "%ENV_FILE%" の DATABASE_URL が正しい PostgreSQL 接続文字列で更新されていることを確認してください
echo    ^(例: postgres://USER:PASSWORD@HOST:PORT/NAME^)。
echo.
echo PostgreSQL サポート用の 'psycopg2' ライブラリは依存関係に含まれており、
echo インストールされているはずです。
echo.
echo データベースと .env ファイルが正しく設定されていることを確認したら、何かキーを押して続行してください...
pause
echo(

REM --- Create Django Migration Files (during initial setup) ---
echo [+] Django マイグレーションファイルを作成/確認しています (初期セットアップ)...
pushd "%SCR_DIR%"
python manage.py makemigrations
set "MAKEMIGRATIONS_ERRORLEVEL=%errorlevel%"
popd
if %MAKEMIGRATIONS_ERRORLEVEL% neq 0 (
    echo [!] エラー: 'makemigrations' の実行に失敗しました。モデル定義を確認してください。
    goto :deactivate_venv_after_setup_error
)

echo     マイグレーションファイルの作成/確認が完了しました。
echo(

REM --- Run Django Migrations (during initial setup) ---
echo [+] Django マイグレーションをデータベースに適用しています (初期セットアップ)...
pushd "%SCR_DIR%"
python manage.py migrate
set "MIGRATE_ERRORLEVEL=%errorlevel%"
popd
if %MIGRATE_ERRORLEVEL% neq 0 (
    echo [!] エラー: 初期セットアップ中のマイグレーションの実行に失敗しました。
    echo     "%ENV_FILE%" のデータベース設定を確認してください。
    echo     - SQLite ^(デフォルト^) の場合: DATABASE_URL が 'sqlite:///db.sqlite3' ^(または同様の SQLite パス^) に設定されていることを確認してください。
    echo       スクリプトは、SQLite ファイルが存在しない場合に作成を試みます。
    echo       失敗した場合は、プロジェクトディレクトリの書き込み権限を確認してください。
    echo     - PostgreSQL の場合: サーバーが実行中でアクセス可能であり、データベース/ユーザーが存在し、
    echo       "%ENV_FILE%" の DATABASE_URL が正しいことを確認してください。
    goto :deactivate_venv_after_setup_error
)
echo     初期マイグレーションが正常に完了しました。
echo(

REM --- Create Superuser (Optional but Recommended, during initial setup) ---
echo [+] 事前定義されたパスワードでスーパーユーザー 'admin' を作成しています...

REM Set environment variables for non-interactive superuser creation
REM Based on the error "CommandError: You must use --custom_id with --noinput.",
REM it's assumed that the USERNAME_FIELD in your CustomUser model is 'custom_id'.
REM If it's different, adjust DJANGO_SUPERUSER_CUSTOM_ID accordingly.
set "DJANGO_SUPERUSER_CUSTOM_ID=admin"
set "DJANGO_SUPERUSER_PASSWORD=admin"

pushd "%SCR_DIR%"
python manage.py createsuperuser --noinput
set "CREATESUPERUSER_ERRORLEVEL=%errorlevel%"
popd
if %CREATESUPERUSER_ERRORLEVEL% neq 0 (
    echo [!] 警告: スーパーユーザー 'admin' の自動作成に失敗しました。
    echo     エラーコード: %errorlevel%. これは、ユーザーが既に存在する場合や、USERNAME_FIELD の設定ミス、
    echo     またはその他の Django 設定の問題が原因である可能性があります。
    echo     (例: カスタムユーザーモデルの USERNAME_FIELD が 'custom_id' ではない場合など)
    echo     手動で作成する必要があるかもしれません: python %MANAGE_PY% createsuperuser
) else (
    echo     スーパーユーザー 'admin' が正常に作成されたか、既に存在します。
)
set "DJANGO_SUPERUSER_CUSTOM_ID="
set "DJANGO_SUPERUSER_PASSWORD="
echo(

REM --- Mark setup as complete ---
echo [+] 初期セットアッププロセスが完了しました。
echo [+] セットアップ完了フラグを作成しています: "%SETUP_COMPLETE_FLAG_FILE%"
type NUL > "%SETUP_COMPLETE_FLAG_FILE%"
if %errorlevel% neq 0 (
    echo [!] エラー: セットアップ完了フラグ "%SETUP_COMPLETE_FLAG_FILE%" の作成に失敗しました。
    echo     エラーコード: %errorlevel%. ディレクトリ "%VENV_DIR%" への書き込み権限を確認してください。
    echo     次回、アプリケーションが再度初期セットアップを実行する可能性があります。
    goto :deactivate_venv_after_setup_error
)
echo     セットアップ完了フラグが作成されました。
echo(
echo [+] アプリケーションの起動に進みます...
echo(
REM Fall through to :run_application

:run_application
REM This label is for subsequent runs or after initial setup completes.

REM --- Activate Virtual Environment (for running application) ---
echo [+] 仮想環境をアクティベートしています...
call "%VENV_DIR%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo [!] エラー: 仮想環境のアクティベートに失敗しました。
    goto :eof_final
)
echo     仮想環境がアクティベートされました。
echo(

REM --- Verify .env file before running Django commands ---
echo [+] .env ファイルの状態を確認しています (%ENV_FILE%)...
if not exist "%ENV_FILE%" (
    echo [!] 重大エラー: 環境ファイル "%ENV_FILE%" が見つかりません。
    echo     このファイルには SECRET_KEY やその他の設定が含まれている必要があります。
    echo     初期セットアップ後に削除された可能性があります。
    echo     セットアップフラグファイル %SETUP_COMPLETE_FLAG_FILE% を削除し、
    echo     このスクリプトを再実行して初期セットアップを再度行ってください。
    pause
    goto :deactivate_venv_and_exit
)
findstr /B /L /C:"SECRET_KEY=" "%ENV_FILE%" >nul
if errorlevel 1 (
    echo [!] 重大エラー: "SECRET_KEY=" が "%ENV_FILE%" に見つかりません。
    echo     .env ファイルは存在しますが、SECRET_KEY が設定されていないようです。
    echo     "%ENV_FILE%" の内容:
    type "%ENV_FILE%"
    echo     このファイルに SECRET_KEY が正しく設定されていることを確認してください。
    echo     または、セットアップフラグファイル %SETUP_COMPLETE_FLAG_FILE% を削除し、
    echo     このスクリプトを再実行して初期セットアップを再度行ってください。
    pause
    goto :deactivate_venv_and_exit
)
echo     .env ファイルは存在し、SECRET_KEY エントリが含まれているようです。
echo(

REM --- Run Django Migrations (always run before server start) ---
echo [+] Django マイグレーションを実行しています...
pushd "%SCR_DIR%"
python manage.py migrate
set "MIGRATE_RUN_ERRORLEVEL=%errorlevel%"
popd
if %MIGRATE_RUN_ERRORLEVEL% neq 0 (
    echo [!] エラー: マイグレーションの実行に失敗しました。
    echo     "%ENV_FILE%" のデータベース設定を確認してください。
    echo     - SQLite ^(デフォルト^) の場合: DATABASE_URL が 'sqlite:///db.sqlite3' ^(または同様の SQLite パス^) に設定されていることを確認してください。
    echo       スクリプトは、SQLite ファイルが存在しない場合に作成を試みます。
    echo       失敗した場合は、プロジェクトディレクトリの書き込み権限を確認してください。
    echo     - PostgreSQL の場合: サーバーが実行中でアクセス可能であり、データベース/ユーザーが存在し、
    echo       "%ENV_FILE%" の DATABASE_URL が正しいことを確認してください。
    goto :deactivate_venv_and_exit
)
echo     マイグレーションが正常に完了しました。
echo(

REM --- Start Development Server ---
echo [+] Django 開発サーバーを起動しています...
echo     アプリケーションには http://127.0.0.1:8000 でアクセスできるはずです。
echo     サーバーを停止するには、このウィンドウで Ctrl+C を押してください。
echo(
pushd "%SCR_DIR%"
python manage.py runserver 0.0.0.0:8000
REM popd will execute after server stops
popd
echo サーバーが停止しました。

:deactivate_venv_and_exit
echo [+] 仮想環境を非アクティブ化しています...
call "%VENV_DIR%\Scripts\deactivate.bat" >nul 2>&1
goto :eof_final

:deactivate_venv_after_setup_error
echo [+] セットアップエラー後、仮想環境を非アクティブ化しています...
call "%VENV_DIR%\Scripts\deactivate.bat" >nul 2>&1
goto :eof_final

:eof_final
echo(
echo セットアップスクリプトが終了しました。
REM pushd で変更したカレントディレクトリを元に戻す
popd
pause
endlocal
