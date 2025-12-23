from app import create_app

app = create_app()
print("Rutas registradas en Flask:")
for rule in app.url_map.iter_rules():
    print(rule)
