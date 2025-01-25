from flask import Flask, request, abort, send_file, render_template
import os
import logging
from datetime import datetime
from waitress import serve

app = Flask(__name__)

# Konfigurationsparameter
VALID_USER_AGENT_PREFIX = "SpecialAgent"
PAYLOAD_DIR = "payloads"  # Verzeichnis, in dem die Payloads gespeichert sind
LOG_FILE = "access.log"  # Log-Datei

# Logging einrichten
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
)

def log_download(ip, user_agent, payload):
    logging.info(f"IP: {ip}, User-Agent: {user_agent}, Payload: {payload}")

@app.route('/')
def index():
    user_agent = request.headers.get('User-Agent', '')

    # Authentifizierung: Prüfe den Präfix von User-Agent
    if not user_agent.startswith(VALID_USER_AGENT_PREFIX):
        return render_template('index.html')  # Fallback auf harmlose Webseite

    # Extrahiere den Payload-Namen aus dem User-Agent
    # Format: <PREFIX>:<PAYLOAD_NAME>
    try:
        payload_name = None
        if ":" in user_agent:
            payload_name = user_agent.split(":")[1]

        if not payload_name:
            raise ValueError("Payload name missing")

        payload_path = os.path.join(PAYLOAD_DIR, payload_name)

        if not os.path.exists(payload_path):
            abort(404, "Payload not found")

        # Logge den Download
        ip = request.remote_addr
        log_download(ip, user_agent, payload_name)

        return send_file(payload_path, as_attachment=True)

    except Exception as e:
        abort(400, str(e))

if __name__ == '__main__':
    if not os.path.exists(PAYLOAD_DIR):
        os.makedirs(PAYLOAD_DIR)

    # Verwenden von 0.0.0.0 mit waitress für den Produktionsmodus
    #serve(app, host='0.0.0.0', port=8080)

    # Verwende localhost zum Testen
    serve(app, host='127.0.0.1', port=8080)


# Testing: curl -A "SpecialAgent:payload.bin" "http://127.0.0.1:8080/"
# Testing: curl -A "WrongAgent" "http://127.0.0.1:8080/"
# Testing: curl -A "SpecialAgent:nonexistent.bin" "http://127.0.0.1:8080/"
