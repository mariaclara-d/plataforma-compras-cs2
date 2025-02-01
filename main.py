from app import create_app  # Importa a função create_app do app.py

# Cria a aplicação Flask
app = create_app()

# Inicia o servidor Flask
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
