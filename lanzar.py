from app import create_app, socketio # Importa tu app y tu instancia de socketio

app = create_app()

if __name__ == "__main__":
    # NUNCA uses waitress aquí.
    # socketio.run es el comando mágico que usa Eventlet automáticamente
    # si está instalado en tu entorno virtual.
    
    print("🚀 Servidor iniciado con Eventlet...")
    
    socketio.run(
        app, 
        host="0.0.0.0", 
        port=5000, 
        debug=False, 
        use_reloader=False
    )