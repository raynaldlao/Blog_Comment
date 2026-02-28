from app import initialize_flask_application

if __name__ == "__main__":
    """
    Main entry point for running the Flask development server.
    """
    app = initialize_flask_application()
    app.run(debug=True)
