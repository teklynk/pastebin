from flask import Flask, request, render_template, redirect, url_for
import sqlite3
import uuid
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

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
        return render_template('raw.html', content=result[0])
    else:
        return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)