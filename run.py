from app import create_app

# Cria a nossa aplicação Flask usando a função que definimos
app = create_app()

if __name__ == '__main__':
    # A linha abaixo liga o servidor. 
    # debug=True é ESSENCIAL para vermos os erros detalhados.
    app.run(host='127.0.0.1', port=5000, debug=True)