from app import initialize_flask_application

if __name__ == "__main__":
    app = initialize_flask_application()
    app.run(debug=True)
