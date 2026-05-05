@echo off
set CARPETA=C:\Dashboard_Serviall

echo [%date% %time%] Iniciando actualizacion...
cd /d %CARPETA%

echo [%date% %time%] Ejecutando captura de Invas...
python captura_invas.py
if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: Fallo la captura de Invas
    exit /b 1
)

echo [%date% %time%] Subiendo datos.json a GitHub via API...
python subir_datos.py

if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: Fallo la subida a GitHub
    exit /b 1
)

echo [%date% %time%] Dashboard actualizado correctamente.
