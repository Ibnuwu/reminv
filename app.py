from flask import Flask, render_template, request, redirect, url_for
import pymysql
import os
from dotenv import load_dotenv
from datetime import date, timedelta

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')

# Koneksi Database
def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'reminv'),
        port=int(os.getenv('DB_PORT', 3306)),
        cursorclass=pymysql.cursors.DictCursor
    )

def init_db():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                difficulty INT DEFAULT 2,
                deadline DATE,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ideas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error DB: {e}")

init_db()

# --- ROUTES ---

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """
                SELECT *, 
                (difficulty * 2 + (DATEDIFF(deadline, CURDATE()) * -1)) as priority_score 
                FROM tasks 
                WHERE status = 'pending'
                ORDER BY priority_score DESC, deadline ASC
            """
            cursor.execute(sql)
            tasks = cursor.fetchall()
        conn.close()
        return render_template('index.html', tasks=tasks, today=date.today())
    except Exception as e:
        return f"Error: {e}"

@app.route('/ideas')
def ideas_page():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM ideas ORDER BY created_at DESC")
            ideas = cursor.fetchall()
        conn.close()
        return render_template('ideas.html', ideas=ideas)
    except Exception as e:
        return f"Error: {e}"

# --- ACTIONS ---

@app.route('/add', methods=['POST'])
def add_task():
    try:
        title = request.form['title']
        difficulty = request.form.get('difficulty', 2) 
        days_str = request.form['days_until']
        calculated_deadline = date.today() + timedelta(days=int(days_str))
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO tasks (title, difficulty, deadline) VALUES (%s, %s, %s)",
                (title, difficulty, calculated_deadline)
            )
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    except Exception as e:
        return f"Gagal: {e}"

# --- ROUTE BARU: PINDAHIN NOTE KE TUGAS DENGAN OPSI ---
@app.route('/promote_idea', methods=['POST'])
def promote_idea():
    try:
        note_id = request.form['note_id']
        title = request.form['title']
        difficulty = request.form.get('difficulty', 2)
        days_str = request.form['days_until']
        
        calculated_deadline = date.today() + timedelta(days=int(days_str))
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 1. Masukin ke Tasks
            cursor.execute(
                "INSERT INTO tasks (title, difficulty, deadline) VALUES (%s, %s, %s)",
                (title, difficulty, calculated_deadline)
            )
            # 2. Hapus dari Ideas (karena udah jadi tugas)
            cursor.execute("DELETE FROM ideas WHERE id = %s", (note_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('index')) # Lempar ke halaman tugas
    except Exception as e:
        return f"Gagal Promote: {e}"

@app.route('/done/<int:id>')
def mark_done(id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("UPDATE tasks SET status = 'done' WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_task(id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM tasks WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/add_idea', methods=['POST'])
def add_idea():
    content = request.form['content']
    if content:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO ideas (content) VALUES (%s)", (content,))
        conn.commit()
        conn.close()
    return redirect(url_for('ideas_page'))

# Route convert_idea yang lama dihapus/tidak dipakai lagi karena diganti promote_idea
@app.route('/convert_idea/<int:id>')
def convert_idea(id):
    return redirect(url_for('ideas_page')) 

@app.route('/delete_idea/<int:id>')
def delete_idea(id):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("DELETE FROM ideas WHERE id = %s", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('ideas_page'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)