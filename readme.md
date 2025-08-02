# Python Pastebin

A simple, self-hosted pastebin web application built with Flask.  
Supports rate limiting, CSRF protection, encrypted contents and automatic cleanup of old pastes.

## Features

- Create and share text pastes with unique URLs
- View raw paste content
- Rate limiting per IP address
- CSRF protection for POST requests
- Encrypted pastes
- Automatic deletion of pastes older than (user defined)
- Configurable via environment variables
- Runs locally or in Docker

## Getting Started

### Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/teklynk/python_paste.git
   cd python_paste
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   - Rename `sample.env` to `.env`
   - Edit `.env` and set your `SECRET_KEY` and `ALLOWED_DOMAIN`

5. **Run the application:**
   ```bash
   python3 python_paste.py
   ```

6. **Deactivate the virtual environment (optional):**
   ```bash
   deactivate
   ```

### Docker Setup

1. **Configure environment variables:**
   - Rename `sample.docker-compose.yml` to `docker-compose.yml`
   - Edit `docker-compose.yml` and set your `SECRET_KEY`, `ALLOWED_DOMAIN` and `ENCRYPTION_KEY` under the `environment` section

2. **Build and run the container:**
   ```bash
   docker-compose up --build
   ```

## Notes
- On first run, the app will generated a `ENCRYPTION_KEY` and save it to the `.env` if it does not already exist. Fernet key must be 32 url-safe base64-encoded bytes.
- If running locally, ensure `.env` is present and configured. `ENCRYPTION_KEY` key must be 32 url-safe base64-encoded bytes.
- If using Docker, configure environment variables in `docker-compose.yml`. Do not use the `.env` file with docker. The `.env` is only needed when running the app locally with `python3 python_paste.py`.
- Pastes older than 90 days are deleted automatically if not defined in `PASTEBIN_EXPIRATION_DAYS`.  
  To disable this, comment out `delete_old_pastes()` in `python_paste.py`.
- The app is designed to work behind a reverse proxy (e.g., Nginx, Cloudflare) and supports real client IP detection.