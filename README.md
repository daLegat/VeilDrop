# VeilDrop
A dead simple covert payload server that selectively delivers malicious implants or redirects to legitimate-looking pages based on request parameters.


# 🚀 Getting Started – Veildrop

Veildrop is a minimal HTTPS-based payload delivery service. The current version is intended for **local testing only**, using self-signed certificates.

---

## 🔐 1. Generate a Self-Signed Certificate

To run the server over HTTPS, you need to generate a certificate and private key:

```bash
mkdir certs
openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/CN=localhost"
```

> This creates `cert.pem` and `key.pem` in the `certs/` folder.

---

## 🚦 2. Run the Server

Start the Flask server locally with HTTPS enabled:

```bash
python veildrop.py
```

The server runs on:  
🔗 https://localhost:8443

You can test it with:

```bash
curl -k -A "SpecialAgent:example_payload.txt" https://localhost:8443/
```

---

## 📄 3. Customize the Web Page

If a visitor does **not** use a valid User-Agent, they will be shown a **legitimate-looking fallback page**.

You can modify this HTML in:

```
templates/index.html
```

> Feel free to make the page look like a real company or service for better social engineering effectiveness.

---

## 📦 4. Add Your Payloads

Payload files must be placed in the `payloads/` directory.  
Example structure:

```
payloads/
├── example_payload.txt
```

Each payload is accessed by setting a User-Agent string like:  
```
SpecialAgent:example_payload.txt
```

Only requests with a valid prefix (`SpecialAgent`) and a known filename will trigger downloads.

---

## 📋 5. Logging

All successful download requests are logged to `access.log`, including:

- Client IP address
- User-Agent string
- Requested payload filename

This helps with auditing and tracking payload distribution.

---

## 🧪 Current Limitations

- Only HTTPS with **self-signed certificates** is supported (for testing).
- No automatic certificate management or production-grade HTTPS yet.
- No built-in authentication beyond User-Agent filtering.

## 🗺️ Roadmap – Planned Improvements for VeilDrop

🕵️‍♂️ **Improve OPSEC and Anti-CTI Measures**  
Enhance operational security by implementing evasion techniques and reducing indicators of compromise to better avoid detection and threat intel feeds.

🔐 **Add More Authentication Options**  
Introduce additional access control mechanisms beyond User-Agent filtering, such as API keys, tokens, mutual TLS, or time-based request validation.

🚀 **Production Mode with Certbot & Reverse Proxy**  
Set up a production-ready deployment pipeline including:
- Automatic HTTPS with Certbot (Let's Encrypt)
- Reverse proxy integration (e.g., Nginx or Caddy)
- Optional containerization with Docker for consistent, portable deployment
