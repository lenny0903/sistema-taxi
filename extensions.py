# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO

db = SQLAlchemy(session_options={"expire_on_commit": False})
socketio = SocketIO(async_mode='eventlet', cors_allowed_origins="*")