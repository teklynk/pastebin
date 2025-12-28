import os, sqlite3, uuid, time, threading
from flask import Flask, request, render_template, make_response, redirect, url_for
from flask_limiter import Limiter
from datetime import datetime, timedelta
from flask_wtf import FlaskForm
from wtforms import TextAreaField
from wtforms.validators import DataRequired
from wtforms import BooleanField
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
# Read expiration days from environment, default to 90 if not set
EXPIRATION_DAYS = int(os.getenv('PASTEBIN_EXPIRATION_DAYS', 90))
# Burn after reading - Number of views left before deletion. default to 3 if not set
BURN_VIEWS = int(os.getenv('BURN_AFTER_READING_VIEWS', 3))

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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            burn_after_reading INTEGER DEFAULT 0,
            views_left INTEGER DEFAULT 3
        )
    ''')
    conn.commit()
    conn.close()

def delete_pastes(days=EXPIRATION_DAYS):
    conn = sqlite3.connect('pastebin.db')
    c = conn.cursor()
    
    cutoff = datetime.now() - timedelta(days=days)
    
    c.execute('''
        DELETE FROM pastes
        WHERE created_at < ?
    ''', (cutoff,))
    
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
@limiter.limit("60 per minute")
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
            burn = 1 if form.burn_after_reading.data else 0
            views_left = BURN_VIEWS if burn else None
            encrypted_content = fernet.encrypt(content.encode())
            paste_id = str(uuid.uuid4())[:32]
            conn = sqlite3.connect('pastebin.db')
            c = conn.cursor()
            c.execute('INSERT INTO pastes (id, content, burn_after_reading, views_left) VALUES (?, ?, ?, ?)', (paste_id, encrypted_content, burn, views_left))
            conn.commit()
            conn.close()
            return redirect(url_for('view_paste', paste_id=paste_id))
    return render_template('index.html', form=form)

@app.route('/<paste_id>')
def view_paste(paste_id):
    conn = sqlite3.connect('pastebin.db')
    c = conn.cursor()
    c.execute('SELECT content, burn_after_reading, views_left FROM pastes WHERE id = ?', (paste_id,))
    result = c.fetchone()
    if result:
        try:
            decrypted_content = fernet.decrypt(result[0]).decode()
        except Exception:
            conn.close()
            return redirect('/')
        burn = result[1]
        views_left = result[2]
        if burn and views_left is not None:
            views_left -= 1
            if views_left <= 0:
                c.execute('DELETE FROM pastes WHERE id = ?', (paste_id,))
            else:
                c.execute('UPDATE pastes SET views_left = ? WHERE id = ?', (views_left, paste_id))
            conn.commit()
        conn.close()
        return render_template('view.html', content=decrypted_content, paste_id=paste_id)
    else:
        conn.close()
        return redirect('/')
    
@app.route('/raw/<paste_id>')
def raw_paste(paste_id):
    conn = sqlite3.connect('pastebin.db')
    c = conn.cursor()
    c.execute('SELECT content, burn_after_reading, views_left FROM pastes WHERE id = ?', (paste_id,))
    result = c.fetchone()
    if result:
        try:
            decrypted_content = fernet.decrypt(result[0]).decode()
        except Exception:
            conn.close()
            return redirect('/')
        burn = result[1]
        views_left = result[2]
        if burn and views_left is not None:
            views_left -= 1
            if views_left <= 0:
                c.execute('DELETE FROM pastes WHERE id = ?', (paste_id,))
            else:
                c.execute('UPDATE pastes SET views_left = ? WHERE id = ?', (views_left, paste_id))
            conn.commit()
        conn.close()
        raw = render_template('raw.txt', content=decrypted_content)
        response = make_response(raw)
        response.headers['Content-Type'] = 'text/plain'
        return response
    else:
        conn.close()
        return redirect('/')

class PasteForm(FlaskForm):
    paste_content = TextAreaField('Paste', validators=[DataRequired()])
    burn_after_reading = BooleanField('Burn after reading')

def daily_cleanup():
    while True:
        delete_pastes()
        time.sleep(86400)  # Sleep for 24 hours

if __name__ == '__main__':
    # Create the database if it does not exist
    init_db()
    # Start background cleanup thread
    threading.Thread(target=daily_cleanup, daemon=True).start()
    # Start the app
    app.run(debug=True, host="0.0.0.0", port=5000)