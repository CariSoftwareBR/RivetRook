@echo off
rem RivetRook launcher (Windows). Add this folder to PATH to run "rivetrook" anywhere.
setlocal
set "SCRIPT=%~dp0..\src\RivetRook.py"

rem Probe by running the interpreter: the Microsoft Store alias is on PATH but cannot run scripts.
python -c "import sys; sys.exit(sys.version_info < (3, 8))" >nul 2>&1 && goto :python
py -3 -c "import sys; sys.exit(sys.version_info < (3, 8))" >nul 2>&1 && goto :py
echo RivetRook: Python 3.8+ not found. Install it with: winget install -e --id Python.Python.3.12
exit /b 1

:python
python "%SCRIPT%" %*
exit /b

:py
py -3 "%SCRIPT%" %*
exit /b
