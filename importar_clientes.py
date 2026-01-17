import csv
import os
from flask import Flask
from extensions import db
from models.clientes import Cliente  # <--- Ruta ajustada

def crear_app_minima():
    app = Flask(__name__)
    # Detectar la ruta absoluta a la DB para evitar errores de archivo no encontrado
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, 'taxis.db')
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def ejecutar_importacion(ruta_csv):
    app = crear_app_minima()
    
    with app.app_context():
        # Verificamos si el archivo existe antes de abrirlo
        if not os.path.exists(ruta_csv):
            print(f"❌ Error: El archivo '{ruta_csv}' no existe.")
            return

        try:
            with open(ruta_csv, mode='r', encoding='utf-8-sig') as f: # utf-8-sig quita el BOM de Excel
                lector = csv.DictReader(f)
                
                nuevos = 0
                saltados = 0
                
                print("⏳ Procesando registros...")
                
                for fila in lector:
                    # Extraer y limpiar datos
                    tel = fila['telefono'].strip()
                    nom = fila['nombre'].strip()
                    dir_cl = fila.get('direccion', '').strip()
                    ref = fila.get('punto_referencia', '').strip()

                    # Validación de integridad: Verificar el UNIQUE(telefono)
                    cliente_existente = Cliente.query.filter_by(telefono=tel).first()
                    
                    if not cliente_existente:
                        nuevo_cliente = Cliente(
                            telefono=tel,
                            nombre=nom,
                            direccion=dir_cl,
                            punto_referencia=ref
                        )
                        db.session.add(nuevo_cliente)
                        nuevos += 1
                    else:
                        saltados += 1
                
                db.session.commit()
                print("-" * 30)
                print(f"✅ ¡Importación Exitosa!")
                print(f"📊 Registros nuevos: {nuevos}")
                print(f"⏭️  Registros saltados: {saltados} (ya existían)")
                print("-" * 30)

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error fatal: {e}")

if __name__ == "__main__":
    # Asegúrate de que el nombre del archivo coincida con el tuyo
    ejecutar_importacion('data_los_patriotas.csv')