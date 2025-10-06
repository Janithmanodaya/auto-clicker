@echo off
setlocal enabledelayedexpansion

rem Creates a local virtual environment (.venv) and installs dependencies from requirements.txt

pushd "%~dp0\.."

if not exist "requirements.txt" (
  echo requirements.txt not found in project root: %cd%
  popd
  exit /b 1
)

set "PYTHON_BIN="

where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_BIN=py -3"
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    set "PYTHON_BIN=python"
  ) else (
    echo Python not found. Please install Python 3.10+.
    popd
    exit /b 1
  )
)

if not exist ".venv" (
  %PYTHON_BIN% -m venv .venv
)

call ".venv\Scripts\activate.bat"

rem Ensure pip exists in the venv (handles cases where pip was not bootstrapped)
python -m ensurepip --upgrade

python -m pip install --upgrade pip wheel setuptools
pip install -r requirements.txt

echo Dependencies installed into virtual environment: %cd%\.venv
echo.
echo To activate the environment in a new shell later, run:
echo   call .venv\Scripts\activate.bat

popd
endlocal