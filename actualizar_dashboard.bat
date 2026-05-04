@echo off
:: ─────────────────────────────────────────────
:: actualizar_dashboard.bat
:: Ejecuta el script de captura y sube datos.json a GitHub
::
:: CONFIGURAR ANTES DE USAR:
:: 1. Cambia CARPETA por la ruta donde tienes los archivos
:: 2. Asegúrate de haber hecho "git clone" del repositorio en esa carpeta
:: ─────────────────────────────────────────────

set CARPETA=C:\Dashboard_Serviall

echo [%date% %time%] Iniciando actualizacion...

:: Ir a la carpeta del proyecto
cd /d %CARPETA%

:: Correr el script Python para extraer datos de Invas
echo [%date% %time%] Ejecutando captura de Invas...
python captura_invas.py

:: Verificar si el script corrió bien
if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: Fallo la captura de Invas
    exit /b 1
)

:: Subir datos.json a GitHub
echo [%date% %time%] Subiendo datos a GitHub...
git add datos.json
git commit -m "Actualizacion automatica %date% %time%"
git push

if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: Fallo el push a GitHub
    exit /b 1
)

echo [%date% %time%] Dashboard actualizado correctamente.
