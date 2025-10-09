@echo off
REM ===================================================================
REM �X�V & �}�C�O���[�V�����������s�o�b�`
REM �v���W�F�N�g���[�g�ɒu���āAShift_JIS (SJIS) �ŕۑ����Ă��������B
REM ===================================================================

setlocal EnableDelayedExpansion

REM --- �X�N���v�g���g�̂���f�B���N�g�����擾 ---
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"

REM --- ���z���� Django �X�N���v�g�̃p�X�ݒ� ---
set "VENV_DIR=%SCRIPT_DIR%venv"
set "SCR_DIR=%SCRIPT_DIR%open_mes\scr"
set "MANAGE_PY=%SCR_DIR%\manage.py"

echo =======================================================
echo  Updating repository and running migrations...
echo =======================================================
echo(

REM --- ���|�W�g���̍X�V ---
echo [1/4] git pull...
git pull
if %errorlevel% neq 0 (
    echo [!] git pull �Ɏ��s���܂����B�l�b�g���[�N�⃊�|�W�g���̏�Ԃ��m�F���Ă��������B
    pause
    goto :cleanup
)
echo     git pull �����B
echo(

REM --- ���z���̃A�N�e�B�x�[�g ---
echo [2/4] Activating virtual environment...
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [!] ���z����������܂���: "%VENV_DIR%\Scripts\activate.bat"
    pause
    goto :cleanup
)
call "%VENV_DIR%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    echo [!] ���z���̃A�N�e�B�x�[�g�Ɏ��s���܂����B
    pause
    goto :cleanup
)
echo     ���z���A�N�e�B�x�[�g�����B
echo(

REM --- makemigrations (�I�v�V����: �K�v�Ȃ�t�@�C���P�ʂ� app ���w�肵�Ă�������) ---
echo [3/4] Making migrations...
pushd "%SCR_DIR%"
python manage.py makemigrations
if %errorlevel% neq 0 (
    echo [!] makemigrations �Ɏ��s���܂����B���f���̕ύX���m�F���Ă��������B
    popd
    pause
    goto :cleanup
)
echo     makemigrations �����B
echo(

REM --- migrate ---
echo [4/4] Applying migrations...
python manage.py migrate
if %errorlevel% neq 0 (
    echo [!] migrate �Ɏ��s���܂����B�f�[�^�x�[�X�ݒ���m�F���Ă��������B
    popd
    pause
    goto :cleanup
)
echo     migrate �����B
popd
echo(
echo =======================================================
echo  Update & migrations complete!
echo =======================================================
pause

:cleanup
REM ���z���̔�A�N�e�B�x�[�g�i�K�v�Ȃ�j
call "%VENV_DIR%\Scripts\deactivate.bat" >nul 2>&1
popd
endlocal