@echo off
cd /d "%~dp0"
if exist html\js rd /s /q html\js
if exist src\__javascript__ rd /s /q src\__javascript__
