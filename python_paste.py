from flask import Flask, request, render_template, make_response, redirect, url_for
import sqlite3
import uuid
from flask_limiter import Limiter
from datetime import datetime, timedelta
from flask_wtf import FlaskForm
from wtforms import TextAreaField
from wtforms.validators import DataRequired
import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

# Check if .env exists (local mode)
LOCAL_MODE = os.path.exists('.env')
if LOCAL_MODE:
    load_dotenv()

# Generate a key using: Fernet.generate_key() and set it in .env
def ensure_encryption_key():
    """Ensure ENCRYPTION_KEY exists in .env, generate and add if missing."""
    encryption_key = os.getenv('ENCRYPTION_KEY')
    if not encryption_key:
        new_key = Fernet.generate_key().decode()
        # Append to .env
        with open('.env', 'a') as env_file:
            env_file.write(f'\nENCRYPTION_KEY={new_key}\n')
        print(f"Generated new ENCRYPTION_KEY and added to .env: {new_key}")
        # Reload .env to pick up the new key
        os.environ['ENCRYPTION_KEY'] = new_key
        return new_key
    return encryption_key

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
encryption_key = ensure_encryption_key()
fernet = Fernet(encryption_key)

def get_real_ip():
    # Use Cloudflare's header if present, else fallback to remote address
    return request.headers.get('CF-Connecting-IP', request.remote_addr)

limiter = Limiter(
    app,
    key_func=get_real_ip
)

def init_db():
    conn = sqlite3.connect('pastebin.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS pastes (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def delete_pastes(days=90):
    conn = sqlite3.connect('pastebin.db')
    c = conn.cursor()
    
    ninety_days_ago = datetime.now() - timedelta(days=days)
    
    c.execute('''
        DELETE FROM pastes
        WHERE created_at < ?
    ''', (ninety_days_ago,))
    
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
@limiter.limit("120 per minute")
def index():
    allowed_domain = os.getenv('ALLOWED_DOMAIN')
    form = PasteForm()
    if request.method == 'POST':
        origin = request.headers.get('Origin')
        referer = request.headers.get('Referer')
        if not origin and not referer:
            return "Forbidden: Missing origin", 403
        if not ((origin and origin.startswith(allowed_domain)) or (referer and referer.startswith(allowed_domain))):
            return "Forbidden: Invalid origin", 403
        if form.validate_on_submit():
            content = form.paste_content.data
            encrypted_content = fernet.encrypt(content.encode())
            paste_id = str(uuid.uuid4())[:8]
            conn = sqlite3.connect('pastebin.db')
            c = conn.cursor()
            c.execute('INSERT INTO pastes (id, content) VALUES (?, ?)', (paste_id, encrypted_content))
            conn.commit()
            conn.close()
            return redirect(url_for('view_paste', paste_id=paste_id))
    return render_template('index.html', form=form)

@app.route('/<paste_id>')
def view_paste(paste_id):
    conn = sqlite3.connect('pastebin.db')
    c = conn.cursor()
    c.execute('SELECT content FROM pastes WHERE id = ?', (paste_id,))
    result = c.fetchone()
    conn.close()
    if result:
        try:
            decrypted_content = fernet.decrypt(result[0]).decode()
        except Exception:
            return redirect('/')
        return render_template('view.html', content=decrypted_content, paste_id=paste_id)
    else:
        return redirect('/')
    
@app.route('/raw/<paste_id>')
def raw_paste(paste_id):
    conn = sqlite3.connect('pastebin.db')
    c = conn.cursor()
    c.execute('SELECT content FROM pastes WHERE id = ?', (paste_id,))
    result = c.fetchone()
    conn.close()
    if result:
        try:
            decrypted_content = fernet.decrypt(result[0]).decode()
        except Exception:
            return redirect('/')
        raw = render_template('raw.txt', content=decrypted_content)
        response = make_response(raw)
        response.headers['Content-Type'] = 'text/plain'
        return response
    else:
        return redirect('/')

class PasteForm(FlaskForm):
    paste_content = TextAreaField('Paste', validators=[DataRequired()])

if __name__ == '__main__':
    # Create the database if it does not exist
    init_db()
    # Delete old pastes older than 90 days
    delete_pastes()
    # Start the Flask application
    app.run(debug=True, host="0.0.0.0", port=5000)