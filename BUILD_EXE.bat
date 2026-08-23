@echo off
chcp 65001 >nul
title Walrus GitHub — сборка EXE
echo ============================================
echo   Walrus GitHub — автоматическая сборка EXE
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ОШИБКА] Python не найден! Установите с https://python.org
    echo При установке отметьте галочку "Add Python to PATH".
    pause
    exit /b 1
)

echo [1/3] Устанавливаю зависимости...
python -m pip install --upgrade pip >nul
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ОШИБКА] Не удалось установить зависимости.
    pause
    exit /b 1
)

echo.
echo [2/3] Собираю EXE (это займёт 1-3 минуты)...
python -m PyInstaller ^
    --noconfirm --onefile --windowed ^
    --name "Walrus GitHub" ^
    --icon "assets\icon.ico" ^
    --add-data "assets\icon.ico;assets" ^
    --add-data "assets\icon_64.png;assets" ^
    --collect-all customtkinter ^
    app.py
if errorlevel 1 (
    echo [ОШИБКА] Сборка не удалась.
    pause
    exit /b 1
)

echo.
echo [3/3] Готово!
echo.
echo   ✔ Ваша программа:  dist\Walrus GitHub.exe
echo.
explorer dist
pause
