@echo off
setlocal enabledelayedexpansion

pushd "%~dp0\.."

rem Ensure venv and deps
if not exist ".venv\Scripts\activate.bat" (
  echo Virtual environment not found. Installing dependencies...
  call "scripts\install_dependencies.bat"
)

if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
)

set "PYTHON_BIN="

rem Prefer the venv's Python if available
if exist ".venv\Scripts\python.exe" (
  set "PYTHON_BIN=.venv\Scripts\python.exe"
) else (
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
      pause
      exit /b 1
    )
  )
)

"%PYTHON_BIN%" --version
"%PYTHON_BIN%" "scripts\build.py" --onefile %*
set "ERR=%ERRORLEVEL%"

if not "%ERR%"=="0" (
  echo.
  echo Build failed. Exit code: %ERR%
  popd
  pause
  exit /b %ERR%
)

echo.
echo Build completed. Check the 'dist' folder.
popd
pause
endlocal