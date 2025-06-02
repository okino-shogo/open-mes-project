@echo off
setlocal

REM --- Configuration ---
set "PROJECT_DIR=%~dp0"
set "VENV_DIR=%PROJECT_DIR%venv"
set "SCR_DIR=%PROJECT_DIR%scr"
set "IMAGE_DIR=%PROJECT_DIR%image"
set "REQUIREMENTS_FILE=%IMAGE_DIR%requirements.txt"
set "MANAGE_PY=%SCR_DIR%manage.py"
set "ENV_FILE=%SCR_DIR%\.env"
set "ENV_EXAMPLE_FILE=%SCR_DIR%\.env.example"
set "SETUP_COMPLETE_FLAG_FILE=%VENV_DIR%\.setup_complete"

REM --- Title ---
title Open MES Project Windows Setup

echo =======================================================
echo  Open MES Project Windows Development Environment Setup
echo =======================================================
echo.

REM --- Check if setup has been completed ---
if exist "%SETUP_COMPLETE_FLAG_FILE%" (
    echo [+] Setup has been completed previously.
    echo [+] Proceeding to start the application...
    echo.
    goto :run_application
)

REM --- Initial Setup Process ---
echo This script will help you set up the project to run on Windows.
echo It assumes it is run from the project root directory.
echo.
echo [+] Starting initial setup...
echo.

REM --- Check for Python and Pip ---
echo [+] Checking for Python and Pip...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] ERROR: Python is not installed or not found in your system's PATH.
    echo     Please install Python 3.11 (from https://www.python.org/)
    echo     and ensure it's added to your PATH during installation.
    goto :eof
)

pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] ERROR: Pip is not installed. This is unusual if Python is installed correctly.
    echo     Please ensure your Python installation includes Pip.
    goto :eof
)
echo     Python and Pip found.
echo.

REM --- Create and Activate Virtual Environment ---
REM Create Virtual Environment
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [+] Creating virtual environment in "%VENV_DIR%"...
    python -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo [!] ERROR: Failed to create virtual environment.
        goto :eof_final
    )
    echo     Virtual environment created successfully.
) else (
    echo [+] Virtual environment already exists at "%VENV_DIR%".
)
echo.
echo [+] Activating virtual environment for setup...
call "%VENV_DIR%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo [!] ERROR: Failed to activate virtual environment.
    goto :eof
)
echo     Virtual environment activated.
echo.

REM --- Install Dependencies (during initial setup) ---
echo [+] Installing dependencies from "%REQUIREMENTS_FILE%"...
pip install -r "%REQUIREMENTS_FILE%"
if %errorlevel% neq 0 (
    echo [!] ERROR: Failed to install dependencies. Please check the error messages above.
    echo     Note: This project is configured to use SQLite by default.
    echo     The dependency 'psycopg2' (for PostgreSQL) is also being installed as per "%REQUIREMENTS_FILE%".
    echo     If errors are related to 'psycopg2':
    echo     1. Ensure PostgreSQL client libraries are installed and in your PATH.
    echo        (This is needed even if you primarily plan to use SQLite, as 'psycopg2' is a listed dependency).
    echo     2. You might need Microsoft Visual C++ Build Tools.
    echo     3. For easier 'psycopg2' installation, you could consider manually editing
    echo        "%REQUIREMENTS_FILE%" to use 'psycopg2-binary' instead of 'psycopg2',
    echo        then re-run this script or 'pip install -r "%REQUIREMENTS_FILE%"' manually.
    echo     A successful installation of all dependencies, including 'psycopg2', is required for initial setup.
    goto :deactivate_venv_after_setup_error
)
echo     Dependencies installed successfully. (Includes 'psycopg2' for optional PostgreSQL use)
echo.

REM --- .env File Setup (during initial setup) ---
echo [+] Checking for .env file at "%ENV_FILE%"...
if not exist "%ENV_FILE%" (
    echo [!] "%ENV_FILE%" not found.
    echo     A default .env file (configured for SQLite) will be created at "%ENV_FILE%".
    echo     A unique SECRET_KEY will be automatically generated.
    echo     Please review the other settings in the generated file.
    echo.

    REM --- Generate SECRET_KEY ---
    echo     Generating a new SECRET_KEY...
    REM Create a temporary Python script to generate the secret key
    (
        echo from django.core.management.utils import get_random_secret_key
        echo print(get_random_secret_key())
    ) > "%SCR_DIR%_generate_secret_key.py"

    REM Execute the script and capture its output (ensure venv is active)
    for /f "delims=" %%i in ('python "%SCR_DIR%_generate_secret_key.py"') do set "GENERATED_SECRET_KEY=%%i"

    REM Delete the temporary script
    if exist "%SCR_DIR%_generate_secret_key.py" del "%SCR_DIR%_generate_secret_key.py"

    if not defined GENERATED_SECRET_KEY (
        echo [!] WARNING: Failed to automatically generate SECRET_KEY. Django might not be installed yet or an error occurred.
        echo            A placeholder key will be used. You MUST change it manually in "%ENV_FILE%".
        set "GENERATED_SECRET_KEY=your_very_secret_and_unique_django_key_here_please_change_me_manually_!!!"
    ) else (
        echo     SECRET_KEY generated successfully.
    )
    echo.

    (
        echo REM Please fill in your actual secret key and database details.
        echo SECRET_KEY=%GENERATED_SECRET_KEY%
        echo.
        echo DEBUG=True
        echo.
        echo ALLOWED_HOSTS=*
        echo REM For local development, you might restrict this, e.g., ALLOWED_HOSTS=localhost,127.0.0.1
        echo.
        echo CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
        echo REM Add other origins if needed, e.g. CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,https://yourdomain.com
        echo.
        echo REM --- Database Configuration (Default: SQLite) ---
        echo DB_ENGINE=django.db.backends.sqlite3
        echo DB_NAME=db.sqlite3
        echo REM The SQLite database file (e.g., db.sqlite3) will typically be created in the directory
        echo REM containing manage.py, or as configured in your Django settings (BASE_DIR).
        echo.
        echo REM --- Optional: PostgreSQL Configuration (if you switch from SQLite) ---
        echo REM To use PostgreSQL, uncomment these lines and fill in your details.
        echo REM Ensure 'psycopg2' or 'psycopg2-binary' is in your requirements.txt.
        echo REM DB_ENGINE=django.db.backends.postgresql
        echo REM DB_NAME=open_mes
        echo REM DB_USER=django
        echo REM DB_PASSWORD=django
        echo REM DB_HOST=localhost
        echo REM DB_PORT=5432
    ) > "%ENV_FILE%"
    echo     Default .env file (configured for SQLite) created at "%ENV_FILE%".
    echo.
    echo     ========================= IMPORTANT ACTION REQUIRED =========================
    echo     1. Review the newly created "%ENV_FILE%". A unique SECRET_KEY has been
    echo        automatically generated. If generation failed, you MUST set it manually.
    echo     2. Confirm other settings like ALLOWED_HOSTS and database configuration.
    echo     3. The default database is SQLite (pre-configured in "%ENV_FILE%").
    echo        The SQLite database file (e.g., db.sqlite3 as per default .env) will be
    echo        created automatically by Django during migrations if it doesn't exist.
    echo     4. If you wish to use PostgreSQL instead, you must edit "%ENV_FILE%"
    echo        with your PostgreSQL server details and ensure it's running.
    echo     ===========================================================================
    echo.
    pause
) else (
    echo     "%ENV_FILE%" found. Please ensure it is correctly configured.
    echo     For SQLite (default): DB_ENGINE=django.db.backends.sqlite3, DB_NAME=db.sqlite3
    echo     And ensure it has a unique SECRET_KEY.
    echo     If using PostgreSQL, ensure connection details are correct.
)
echo.

REM --- Database Setup Reminder (during initial setup) ---
echo =====================================
echo  DATABASE SETUP
echo =====================================
echo This project is configured to use SQLite by default.
echo 1. Ensure your "%ENV_FILE%" has a unique SECRET_KEY.
echo 2. The SQLite database (e.g., 'db.sqlite3' as per default .env) will be
echo    created automatically by Django during migrations if it doesn't exist.
echo    Ensure DB_ENGINE is 'django.db.backends.sqlite3' and DB_NAME is set in "%ENV_FILE%".
echo.
echo If you have chosen to use PostgreSQL instead (by modifying "%ENV_FILE%"):
echo 1. Ensure PostgreSQL server is installed and running.
echo 2. You have created the database and user with necessary permissions.
echo 3. Your "%ENV_FILE%" is updated with the correct PostgreSQL connection details
echo    (DB_ENGINE, DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT).
echo.
echo The 'psycopg2' library for PostgreSQL support is included in the dependencies
echo and should have been installed.
echo.
echo Press any key to continue once you have confirmed the database and .env file are correctly set up...
pause
echo.

REM --- Run Django Migrations (during initial setup) ---
echo [+] Running Django migrations (initial setup)...
python "%MANAGE_PY%" migrate
if %errorlevel% neq 0 (
    echo [!] ERROR: Failed to run migrations during initial setup.
    echo     Please check your database settings in "%ENV_FILE%".
    echo     - For SQLite (default): Ensure DB_ENGINE='django.db.backends.sqlite3' and DB_NAME is specified.
    echo       The script attempts to create the SQLite file if it doesn't exist.
    echo       Check for write permissions in the project directory if it fails.
    echo     - For PostgreSQL: Ensure the server is running, accessible, the database/user exist,
    echo       and credentials in "%ENV_FILE%" are correct.
    goto :deactivate_venv_after_setup_error
)
echo     Initial migrations completed successfully.
echo.

REM --- Create Superuser (Optional but Recommended, during initial setup) ---
echo [+] You might want to create a superuser to access the Django admin panel.
set /p createsuperuser="Do you want to create a superuser now? (y/N): "
if /i "%createsuperuser%"=="y" (
    echo     Running createsuperuser command...
    python "%MANAGE_PY%" createsuperuser
)
echo.

REM --- Mark setup as complete ---
echo [+] Initial setup process complete.
echo [+] Creating setup completion flag: "%SETUP_COMPLETE_FLAG_FILE%"
echo.> "%SETUP_COMPLETE_FLAG_FILE%"
if %errorlevel% neq 0 (
    echo [!] ERROR: Failed to create setup completion flag.
    echo     The application might run the initial setup again next time.
    goto :deactivate_venv_after_setup_error
)
echo     Setup completion flag created.
echo.
echo [+] Proceeding to start the application...
echo.
REM Fall through to :run_application

:run_application
REM This label is for subsequent runs or after initial setup completes.

REM --- Activate Virtual Environment (for running application) ---
echo [+] Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo [!] ERROR: Failed to activate virtual environment.
    goto :eof_final
)
echo     Virtual environment activated.
echo.

REM --- Run Django Migrations (always run before server start) ---
echo [+] Running Django migrations...
python "%MANAGE_PY%" migrate
if %errorlevel% neq 0 (
    echo [!] ERROR: Failed to run migrations.
    echo     Please check your database settings in "%ENV_FILE%".
    echo     - For SQLite (default): Ensure DB_ENGINE='django.db.backends.sqlite3' and DB_NAME is specified.
    echo       The script attempts to create the SQLite file if it doesn't exist.
    echo       Check for write permissions in the project directory if it fails.
    echo     - For PostgreSQL: Ensure the server is running, accessible, the database/user exist,
    echo       and credentials in "%ENV_FILE%" are correct.
    goto :deactivate_venv_and_exit
)
echo     Migrations completed successfully.
echo.

REM --- Start Development Server ---
echo [+] Starting Django development server...
echo     You should be able to access the application at: http://127.0.0.1:8000
echo     Press Ctrl+C in this window to stop the server.
echo.
python "%MANAGE_PY%" runserver 0.0.0.0:8000

echo Server stopped.

:deactivate_venv_and_exit
echo [+] Deactivating virtual environment...
call "%VENV_DIR%\Scripts\deactivate.bat" >nul 2>&1
goto :eof_final

:deactivate_venv_after_setup_error
echo [+] Deactivating virtual environment after setup error...
call "%VENV_DIR%\Scripts\deactivate.bat" >nul 2>&1
goto :eof_final

:eof_final
echo.
echo Setup script finished.
pause
endlocal
