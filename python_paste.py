from flask import Flask, request, render_template, make_response, redirect, url_for
import sqlite3
import uuid
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta

app = Flask(__name__)

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["6000 per day", "600 per hour"]
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

def delete_old_pastes(days=90):
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
@limiter.limit("50 per minute")
def index():
    if request.method == 'POST':
        content = request.form['paste_content']
        paste_id = str(uuid.uuid4())[:8]
        conn = sqlite3.connect('pastebin.db')
        c = conn.cursor()
        c.execute('INSERT INTO pastes (id, content) VALUES (?, ?)', (paste_id, content))
        conn.commit()
        conn.close()
        return redirect(url_for('view_paste', paste_id=paste_id))
    return render_template('index.html')

@app.route('/<paste_id>')
def view_paste(paste_id):
    conn = sqlite3.connect('pastebin.db')
    c = conn.cursor()
    c.execute('SELECT content FROM pastes WHERE id = ?', (paste_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return render_template('view.html', content=result[0], paste_id=paste_id)
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
        raw = render_template('raw.txt', content=result[0])
        response = make_response(raw)
        response.headers['Content-Type'] = 'text/plain'
        return response
    else:
        return redirect('/')

if __name__ == '__main__':
    # Create the database if it does not exist
    init_db()
    # Delete old pastes older than 90 days
    delete_old_pastes()
    # Start the Flask application
    app.run(debug=True, host="0.0.0.0", port=5000)