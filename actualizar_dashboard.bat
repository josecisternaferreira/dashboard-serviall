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

echo [%date% %time%] Subiendo datos a GitHub...
git add datos.json
git commit -m "Actualizacion automatica %date% %time%"
git push origin main --force

echo [%date% %time%] Dashboard actualizado correctamente.
