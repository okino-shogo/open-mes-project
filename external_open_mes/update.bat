@echo off
REM ===================================================================
REM 更新 & マイグレーション自動実行バッチ
REM プロジェクトルートに置いて、Shift_JIS (SJIS) で保存してください。
REM ===================================================================

setlocal EnableDelayedExpansion

REM --- スクリプト自身のあるディレクトリを取得 ---
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"

REM --- 仮想環境と Django スクリプトのパス設定 ---
set "VENV_DIR=%SCRIPT_DIR%venv"
set "SCR_DIR=%SCRIPT_DIR%open_mes\scr"
set "MANAGE_PY=%SCR_DIR%\manage.py"

echo =======================================================
echo  Updating repository and running migrations...
echo =======================================================
echo(

REM --- リポジトリの更新 ---
echo [1/4] git pull...
git pull
if %errorlevel% neq 0 (
    echo [!] git pull に失敗しました。ネットワークやリポジトリの状態を確認してください。
    pause
    goto :cleanup
)
echo     git pull 完了。
echo(

REM --- 仮想環境のアクティベート ---
echo [2/4] Activating virtual environment...
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [!] 仮想環境が見つかりません: "%VENV_DIR%\Scripts\activate.bat"
    pause
    goto :cleanup
)
call "%VENV_DIR%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo [!] 仮想環境のアクティベートに失敗しました。
    pause
    goto :cleanup
)
echo     仮想環境アクティベート完了。
echo(

REM --- makemigrations (オプション: 必要ならファイル単位で app を指定してください) ---
echo [3/4] Making migrations...
pushd "%SCR_DIR%"
python manage.py makemigrations
if %errorlevel% neq 0 (
    echo [!] makemigrations に失敗しました。モデルの変更を確認してください。
    popd
    pause
    goto :cleanup
)
echo     makemigrations 完了。
echo(

REM --- migrate ---
echo [4/4] Applying migrations...
python manage.py migrate
if %errorlevel% neq 0 (
    echo [!] migrate に失敗しました。データベース設定を確認してください。
    popd
    pause
    goto :cleanup
)
echo     migrate 完了。
popd
echo(
echo =======================================================
echo  Update & migrations complete!
echo =======================================================
pause

:cleanup
REM 仮想環境の非アクティベート（必要なら）
call "%VENV_DIR%\Scripts\deactivate.bat" >nul 2>&1
popd
endlocal