from flask import Flask, render_template, request, redirect, url_for
import pymysql
import os
from dotenv import load_dotenv
from datetime import date

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')

# Fungsi Koneksi Database
def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        port=int(os.getenv('DB_PORT', 3306)), # Pastikan port angka integer
        cursorclass=pymysql.cursors.DictCursor
    )

# --- FUNGSI BARU: Bikin Tabel Otomatis (Self-Healing) ---
def init_db():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Bikin tabel kalau belum ada
            sql = """
            CREATE TABLE IF NOT EXISTS tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                difficulty INT DEFAULT 2,
                deadline DATE,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            cursor.execute(sql)
        conn.commit()
        conn.close()
        print("Database aman! Tabel tasks siap.")
    except Exception as e:
        print(f"Error connect database: {e}")

# Panggil fungsi ini sekali saat aplikasi nyala
init_db()

# --- ROUTES ---
@app.route('/')
def index():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Logika Prioritas: Status -> Score (Difficulty & Deadline)
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
        return f"Terjadi kesalahan database: {e}"

@app.route('/add', methods=['POST'])
def add_task():
    try:
        title = request.form['title']
        difficulty = request.form['difficulty']
        deadline = request.form['deadline']
        
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO tasks (title, difficulty, deadline) VALUES (%s, %s, %s)",
                (title, difficulty, deadline)
            )
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    except Exception as e:
        return f"Gagal nambah tugas: {e}"

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

if __name__ == '__main__':
    # UPDATE PENTING: Ambil PORT dari Railway, kalau gak ada pake 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)