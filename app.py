from flask import Flask, render_template, request, redirect, url_for
import pymysql
import os
from dotenv import load_dotenv
from datetime import date

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Koneksi Database (Bisa auto-reconnect)
def get_db_connection():
    return pymysql.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/')
def index():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        # LOGIKA CERDAS: Urutkan berdasarkan Status (Pending dulu), 
        # lalu Prioritas (Difficulty tinggi + Deadline mepet naik ke atas)
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

@app.route('/add', methods=['POST'])
def add_task():
    title = request.form['title']
    difficulty = request.form['difficulty'] # 1, 2, atau 3
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
    # Debug=True biar kalau error kelihatan di browser
    app.run(debug=True, host='0.0.0.0', port=5000)