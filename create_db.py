import sqlite3

def init_db():
    conn = sqlite3.connect('pastebin.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS pastes (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()