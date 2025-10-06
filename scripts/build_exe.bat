@echo off
setlocal

pushd "%~dp0\.."

if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
)

python --version
python "scripts\build.py" --onefile %*

echo Build completed. Check the 'dist' folder.
popd
endlocal