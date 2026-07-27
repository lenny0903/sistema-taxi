@echo off
set PYTHONIOENCODING=utf-8
chcp 65001

:: Cambia a la carpeta del proyecto
cd /d "C:\Users\Admin\app_taxis"

echo Levantando servidor Waitress en el puerto 5000...
python -m waitress --call --host=0.0.0.0 --port=5000 app:create_app

pause