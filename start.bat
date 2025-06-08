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
            REM Check if the temp file is not empty
            for /F "usebackq" %%A in ("%SECRET_KEY_TEMP_LINE_FILE%") do set "line_not_empty=1"
            if defined line_not_empty (
                echo     SECRET_KEY が正常に生成されました。
                copy /Y "%SECRET_KEY_TEMP_LINE_FILE%" "%ENV_FILE%" > nul
                GOTO :secret_key_written_to_env
            ) else (
                echo     デバッグ: Pythonは成功しましたが、出力ファイル "%SECRET_KEY_TEMP_LINE_FILE%" が空です。
            )
        ) else (
            echo     デバッグ: Pythonは成功しましたが、出力ファイル "%SECRET_KEY_TEMP_LINE_FILE%" が見つかりません。
        )
    )

    REM Fallthrough to here means SECRET_KEY generation failed
:handle_secret_key_generation_failure
        echo [!] 警告: SECRET_KEY の自動生成に失敗しました。
        echo            Django がまだインストールされていないか、Python スクリプト実行中にエラーが発生した可能性があります。
        echo            プレースホルダーキーが使用されます。"%ENV_FILE%" で手動で変更する必要があります。
        (echo SECRET_KEY=your_very_secret_and_unique_django_key_here_please_change_me_manually_!!!) > "%ENV_FILE%"

:secret_key_written_to_env
    if exist "%SECRET_KEY_TEMP_LINE_FILE%" del "%SECRET_KEY_TEMP_LINE_FILE%"
    echo(

    REM Append other settings to .env file
    echo DEBUG=True >> "%ENV_FILE%"
    echo ALLOWED_HOSTS=* >> "%ENV_FILE%"
    echo CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000 >> "%ENV_FILE%"
    echo DB_ENGINE=django.db.backends.sqlite3 >> "%ENV_FILE%"
    echo DB_NAME=db.sqlite3 >> "%ENV_FILE%"
    echo     デフォルトの .env ファイル ^(SQLite 用に設定済み^) が "%ENV_FILE%" に作成されました。
    echo(
    echo     ========================= 重要: 対応が必要です =========================
    echo     1. 新しく作成された "%ENV_FILE%" を確認してください。一意の SECRET_KEY が
    echo        自動的に生成されました。生成に失敗した場合は、手動で設定する必要があります。
    echo     2. ALLOWED_HOSTS やデータベース設定など、他の設定を確認してください。    
    echo     3. デフォルトのデータベースは SQLite です ^("%ENV_FILE%" で事前設定済み^)。
    echo        SQLite データベースファイル ^(例: デフォルトの .env に従い db.sqlite3^) は、
    echo        存在しない場合、マイグレーション中に Django によって自動的に作成されます。
    echo     4. 代わりに PostgreSQL を使用する場合は、"%ENV_FILE%" を編集し、
    echo        PostgreSQL サーバーの詳細を入力し、実行されていることを確認する必要があります。
    echo     ===========================================================================
    echo(
    pause    
    GOTO :after_env_file_handling

:handle_env_file_exists
    REM This is the block for when .env DOES exist
    echo DEBUG: Point F - ENV_FILE exists.
    echo     %ENV_FILE% が見つかりました。正しく設定されていることを確認してください。
    echo     SQLite ^(デフォルト^) の場合: DB_ENGINE=django.db.backends.sqlite3, DB_NAME=db.sqlite3
    echo     そして、一意の SECRET_KEY が設定されていることを確認してください。
    echo     PostgreSQL を使用する場合は、接続詳細が正しいことを確認してください。
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
echo    DB_ENGINE が 'django.db.backends.sqlite3' であり、DB_NAME が "%ENV_FILE%" に設定されていることを確認してください。
echo.
echo 代わりに PostgreSQL を使用することを選択した場合 ("%ENV_FILE%" を変更した場合):
echo 1. PostgreSQL サーバーがインストールされ、実行されていることを確認してください。
echo 2. 必要な権限を持つデータベースとユーザーを作成済みであることを確認してください。
echo 3. "%ENV_FILE%" が正しい PostgreSQL 接続詳細で更新されていることを確認してください
echo    (DB_ENGINE, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT)。
echo.
echo PostgreSQL サポート用の 'psycopg2' ライブラリは依存関係に含まれており、
echo インストールされているはずです。
echo.
echo データベースと .env ファイルが正しく設定されていることを確認したら、何かキーを押して続行してください...
pause
echo(

REM --- Run Django Migrations (during initial setup) ---
echo [+] Django マイグレーションを実行しています (初期セットアップ)...
python "%MANAGE_PY%" migrate
if %errorlevel% neq 0 (
    echo [!] エラー: 初期セットアップ中のマイグレーションの実行に失敗しました。
    echo     "%ENV_FILE%" のデータベース設定を確認してください。
    echo     - SQLite ^(デフォルト^) の場合: DB_ENGINE='django.db.backends.sqlite3' であり、DB_NAME が指定されていることを確認してください。
    echo       スクリプトは、SQLite ファイルが存在しない場合に作成を試みます。
    echo       失敗した場合は、プロジェクトディレクトリの書き込み権限を確認してください。
    echo     - PostgreSQL の場合: サーバーが実行中でアクセス可能であり、データベース/ユーザーが存在し、
    echo       "%ENV_FILE%" の認証情報が正しいことを確認してください。
    goto :deactivate_venv_after_setup_error
)
echo     初期マイグレーションが正常に完了しました。
echo(

REM --- Create Superuser (Optional but Recommended, during initial setup) ---
echo [+] 事前定義されたパスワードでスーパーユーザー 'admin' を作成しています...

REM Set environment variables for non-interactive superuser creation
set "DJANGO_SUPERUSER_USERNAME=admin"
set "DJANGO_SUPERUSER_PASSWORD=admin"

python "%MANAGE_PY%" createsuperuser --noinput
if %errorlevel% neq 0 (
    echo [!] 警告: スーパーユーザー 'admin' の自動作成に失敗しました。
    echo     これは、ユーザーが既に存在する場合や、別のエラーが発生した場合に起こる可能性があります。
    echo     手動で作成する必要があるかもしれません: python manage.py createsuperuser
) else (
    echo     スーパーユーザー 'admin' が正常に作成されたか、既に存在します。
)
set "DJANGO_SUPERUSER_USERNAME="
set "DJANGO_SUPERUSER_PASSWORD="
echo(

REM --- Mark setup as complete ---
echo [+] 初期セットアッププロセスが完了しました。
echo [+] セットアップ完了フラグを作成しています: "%SETUP_COMPLETE_FLAG_FILE%"
echo.> "%SETUP_COMPLETE_FLAG_FILE%"
if %errorlevel% neq 0 (
    echo [!] エラー: セットアップ完了フラグの作成に失敗しました。
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

REM --- Run Django Migrations (always run before server start) ---
echo [+] Django マイグレーションを実行しています...
python "%MANAGE_PY%" migrate
if %errorlevel% neq 0 (
    echo [!] エラー: マイグレーションの実行に失敗しました。
    echo     "%ENV_FILE%" のデータベース設定を確認してください。
    echo     - SQLite ^(デフォルト^) の場合: DB_ENGINE='django.db.backends.sqlite3' であり、DB_NAME が指定されていることを確認してください。
    echo       スクリプトは、SQLite ファイルが存在しない場合に作成を試みます。
    echo       失敗した場合は、プロジェクトディレクトリの書き込み権限を確認してください。
    echo     - PostgreSQL の場合: サーバーが実行中でアクセス可能であり、データベース/ユーザーが存在し、
    echo       "%ENV_FILE%" の認証情報が正しいことを確認してください。
    goto :deactivate_venv_and_exit
)
echo     マイグレーションが正常に完了しました。
echo(

REM --- Start Development Server ---
echo [+] Django 開発サーバーを起動しています...
echo     アプリケーションには http://127.0.0.1:8000 でアクセスできるはずです。
echo     サーバーを停止するには、このウィンドウで Ctrl+C を押してください。
echo(
python "%MANAGE_PY%" runserver 0.0.0.0:8000

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
