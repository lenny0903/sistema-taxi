from extensions import db
from app import create_app
from models import Cliente, Reserva
import datetime

def main():
    app = create_app()   # aquí creas la instancia
    with app.app_context():
        cliente = Cliente(nombre="Prueba", telefono="555123", direccion="Centro")
        db.session.add(cliente)
        db.session.commit()

        reserva = Reserva(
            cliente_id=cliente.id_cliente,
            origen="San Cristóbal",
            destino="Táriba",
            fecha=datetime.date(2026, 1, 5),
            hora=datetime.time(14, 30)
        )
        db.session.add(reserva)
        db.session.commit()

        print("Cliente creado con ID:", cliente.id_cliente)
        print("Reserva creada con ID:", reserva.id_reserva)

if __name__ == "__main__":
    main()

