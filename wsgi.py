# wsgi.py
from app import create_app

# Al importar create_app, se ejecuta toda la configuración, 
# incluyendo el Scheduler y la DB.
app = create_app()

# NO necesitamos 'if __name__ == "__main__":' aquí si usarás waitress-serve.
# Si quieres poder hacer "python wsgi.py" para probar, 
# entonces sí déjalo pero SIN el socketio.run.