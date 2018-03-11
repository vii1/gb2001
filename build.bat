@echo off
setlocal
set MAIN=gb2001
cd /d "%~dp0"
if /i "%1"=="release" (
	transcrypt -b src\%MAIN%.py
	if errorlevel 1 goto error
	if exist html\js rd /s /q html\js
	mkdir html\js
	copy /y src\__javascript__\%MAIN%.min.js html\js\%MAIN%.js
) else (
	::transcrypt -n -m -dc -da src\%MAIN%.py
    transcrypt -n src\%MAIN%.py
	if errorlevel 1 goto error
	robocopy src\__javascript__ html\js /s /njh /njs
	if errorlevel 8 goto error
)

goto :eof
:error
pause
exit /b 1
