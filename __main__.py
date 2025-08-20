import logging
from flask import Flask
from dotenv import load_dotenv
from src.routes.documents import documents_bp

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.register_blueprint(documents_bp)

    return app

logging.basicConfig(filename='document-ingestion.log', level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

def main():
    """
    Main entry point for the Flask document ingestion API.
    Starts the web server to group articles via HTTP POST requests.
    """
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    main()
