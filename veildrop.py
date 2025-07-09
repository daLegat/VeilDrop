from flask import Flask, request, abort, send_file, render_template
import os
import logging
from datetime import datetime
from OpenSSL import crypto, SSL
import argparse

app = Flask(__name__)



def log_download(ip, user_agent, payload):
    logging.info(f"IP: {ip}, User-Agent: {user_agent}, Payload: {payload}")


def generate_selfsigned_certificate(
    emailAddress="ssladmin@veildrop.com",
    commonName="VeilDrop",
    countryName="AT",
    stateOrProvinceName="Vienna",
    localityName="Vienna",
    organizationName="VeilDrop",
    organizationUnitName="VeilDrop",
    serialNumber=0,
    validityStartInSeconds=0,
    validityEndInSeconds=10*365*24*60*60,
    KEY_FILE="certs/key.pem",
    CERT_FILE="certs/cert.pem"):
    """function to generate selfsigned certificates

    Args:
        emailAddress (str, optional): _description_. Defaults to "ssladmin@veildrop.com".
        commonName (str, optional): _description_. Defaults to "VeilDrop".
        countryName (str, optional): _description_. Defaults to "AT".
        stateOrProvinceName (str, optional): _description_. Defaults to "Vienna".
        localityName (str, optional): _description_. Defaults to "Vienna".
        organizationName (str, optional): _description_. Defaults to "VeilDrop".
        organizationUnitName (str, optional): _description_. Defaults to "VeilDrop".
        serialNumber (int, optional): _description_. Defaults to 0.
        validityStartInSeconds (int, optional): _description_. Defaults to 0.
        validityEndInSeconds (_type_, optional): _description_. Defaults to 10*365*24*60*60.
        KEY_FILE (str, optional): _description_. Defaults to "certs/key.pem".
        CERT_FILE (str, optional): _description_. Defaults to "certs/cert.pem".
    """
    # generate keys
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 4096)
    #generate cert
    cert = crypto.X509()
    # set cert parameters
    cert.get_subject().C = countryName
    cert.get_subject().ST = stateOrProvinceName
    cert.get_subject().L = localityName
    cert.get_subject().O = organizationName
    cert.get_subject().OU = organizationUnitName
    cert.get_subject().CN = commonName
    cert.get_subject().emailAddress = emailAddress
    cert.set_serial_number(serialNumber)
    cert.gmtime_adj_notBefore(validityStartInSeconds)
    cert.gmtime_adj_notAfter(validityEndInSeconds)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    # sign cert
    cert.sign(k, 'sha512')
    # write key and cert
    with open(CERT_FILE, "wt") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))
    with open(KEY_FILE, "wt") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode("utf-8"))


@app.route('/')
def index():
    user_agent = request.headers.get('User-Agent', '')

    # Authentication: Check the prefix of the user-agent 
    if not user_agent.startswith(args.secret):
        return render_template('index.html')  # Fallback to the legitimate site

    # Extract the payload name from the submitted user agent
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

        # Log the download
        ip = request.remote_addr
        log_download(ip, user_agent, payload_name)

        return send_file(payload_path, as_attachment=True)

    except Exception as e:
        abort(400, str(e))

if __name__ == '__main__':
    # create argparser and parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("IP", help="The IP-address veildrop should listen on")
    parser.add_argument("port", help="The port veildrop should use")
    parser.add_argument("secret", help="The secret that the agent will use to authenticate")
    parser.add_argument("-c", "--certmode",type=str, choices=["selfsigned","certbot"], help="Control whether to generate selfsigned certiicates or use certbot")
    parser.add_argument("-v", "--verbosity", type=int, choices=[0, 1, 2],
                    help="increase output verbosity")
    parser.add_argument("-p", "--payload", type=str, help="Path that Veildrop will server the payloads from")
    args = parser.parse_args()
    
    
    # Handle payload directory argument
    if args.payload is not None:
        PAYLOAD_DIR = args.payload
    else:
        PAYLOAD_DIR = "payloads"
    if not os.path.exists(PAYLOAD_DIR):
        os.makedirs(PAYLOAD_DIR)
        
        
    # Handle certificate argument
    if not os.path.exists("certs"):
        os.mkdir("certs")
        
    if not os.path.exists("logs"):
        os.mkdir("logs")


    # Handle logging argument
    if args.verbosity is None:
            log_level = 0
    else:
        log_level = args.verbosity
    # logging formatter
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
    rootLogger = logging.getLogger()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/log_{timestamp}.log"

    if log_level == 0:
        # Set logger to "no log" (send log to /dev/null)
        nullHandler = logging.NullHandler()
        rootLogger.addHandler(nullHandler)
        rootLogger.setLevel(logging.CRITICAL) 
    elif log_level == 1:
        # Log only to file
        fileHandler = logging.FileHandler(log_filename)
        fileHandler.setFormatter(logFormatter)
        rootLogger.addHandler(fileHandler)
        rootLogger.setLevel(logging.INFO)  
    elif log_level == 2:
        # Log to both file and console
        fileHandler = logging.FileHandler(log_filename)
        fileHandler.setFormatter(logFormatter)
        rootLogger.addHandler(fileHandler)
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        rootLogger.addHandler(consoleHandler)
        rootLogger.setLevel(logging.DEBUG)
        
        
        
        
    if args.certmode == "selfsigned":
        # TODO: make custom attributes of certificate possible
        # handle over interactive session, config file or make both possible?
        generate_selfsigned_certificate()
    if args.certmode == "certbot":
        # TODO: implement LetsEncrypt certificate requesting (probably best over DNS challenge)
        pass
    else:
        if not os.path.isfile("certs/key.pem") and not os.path.isfile("certs/cert.pem"):
            generate_selfsigned_certificate()
        # HTTPS context
    context = ('certs/cert.pem', 'certs/key.pem')

    # Run Flask's built-in HTTPS server (good for local testing)
    app.run(host=args.IP, port=args.port, ssl_context=context)


# Testing: curl -k -A "SpecialAgent:payload.bin" "http://127.0.0.1:8080/"
# Testing: curl -k -A "WrongAgent" "http://127.0.0.1:8080/"
# Testing: curl -k -A "SpecialAgent:nonexistent.bin" "http://127.0.0.1:8080/"
