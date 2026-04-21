@echo off
REM Weekly dependency audit runner (Windows Task Scheduler)

cd /d "%~dp0"

REM Run via Git Bash — UV lives in the user's Scripts dir.
"C:\Program Files\Git\bin\bash.exe" -c "export PATH=$PATH:$HOME/.local/bin && uv run python deps_audit.py"

set EXIT=%ERRORLEVEL%

if %EXIT% EQU 0 (
    echo %date% %time% - Deps audit OK >> deps_audit_runs.log
) else (
    echo %date% %time% - Deps audit HIGH/CRITICAL or error exit=%EXIT% >> deps_audit_runs.log
)

exit /b %EXIT%
