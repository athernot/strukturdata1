# main.py

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import os

app = Flask(__name__)
# [BARU] Kunci rahasia diperlukan untuk sesi dan pesan flash
app.secret_key = 'kunci_rahasia_super_aman_yang_harus_diganti'

# Lokasi database
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gudang.db')

def get_db_connection():
    """Membuat koneksi ke database SQLite."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# === [BARU] DECORATOR UNTUK OTENTIKASI ===
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Anda harus login untuk mengakses halaman ini.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Anda harus login untuk mengakses halaman ini.', 'warning')
            return redirect(url_for('login'))
        if session.get('user_role') != 'admin':
            flash('Anda tidak memiliki izin untuk mengakses halaman ini.', 'danger')
            return redirect(url_for('admin_home')) # atau halaman lain
        return f(*args, **kwargs)
    return decorated_function

# === [BARU] RUTE OTENTIKASI ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_role'] = user['role']
            flash(f"Selamat datang, {user['username']}!", 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_home'))
            else:
                # Arahkan user biasa ke halaman utama user
                return redirect(url_for('index'))
        else:
            flash('Username atau password salah.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            flash('Registrasi berhasil! Silakan login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username sudah digunakan. Silakan pilih yang lain.', 'danger')
        finally:
            conn.close()
            
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah berhasil logout.', 'info')
    return redirect(url_for('login'))


# --- Rute User (Tidak perlu login) ---
@app.route('/')
def index():
    return render_template('user/index.html')

@app.route('/tentang')
def tentang():
    return render_template('user/tentang.html')

@app.route('/kontak')
def kontak():
    return render_template('user/kontak.html')

# --- Rute Admin (Dilindungi) ---

@app.route('/admin/home')
@login_required
def admin_home():
    return render_template('admin/index.html')

@app.route('/admin/admin-kelola-barang')
@admin_required
def kelolabarang():
    # Arahkan ke gudang karena barang.html statis
    return redirect(url_for('kelolagudang'))

@app.route('/admin/admin-kelola-gudang')
@admin_required
def kelolagudang():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM gudang ORDER BY tanggal DESC').fetchall()
    conn.close()
    return render_template('admin/gudang.html', items=items)

@app.route('/admin/admin-laporan')
@admin_required
def laporan():
    return render_template('admin/laporan.html')

@app.route('/admin/gudang/add', methods=['POST'])
@admin_required
def add_item():
    if request.method == 'POST':
        id_barang = request.form['id_barang']
        nama_barang = request.form['nama_barang']
        tanggal = request.form['tanggal']
        jumlah = request.form['jumlah']

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO gudang (id_barang, nama_barang, tanggal, jumlah) VALUES (?, ?, ?, ?)',
                         (id_barang, nama_barang, tanggal, int(jumlah)))
            conn.commit()
            flash('Barang berhasil ditambahkan!', 'success')
        except sqlite3.IntegrityError:
            flash('ID Barang sudah ada, gunakan ID lain.', 'danger')
        finally:
            conn.close()
        
        return redirect(url_for('kelolagudang'))
    return redirect(url_for('kelolagudang'))

@app.route('/admin/gudang/edit/<int:id>', methods=['POST'])
@admin_required
def edit_item(id):
    if request.method == 'POST':
        id_barang_form = request.form['id_barang']
        nama_barang_form = request.form['nama_barang']
        tanggal_form = request.form['tanggal']
        jumlah_form = request.form['jumlah']
        
        conn = get_db_connection()
        conn.execute('UPDATE gudang SET id_barang = ?, nama_barang = ?, tanggal = ?, jumlah = ? WHERE id = ?',
                     (id_barang_form, nama_barang_form, tanggal_form, int(jumlah_form), id))
        conn.commit()
        conn.close()
        flash('Data barang berhasil diperbarui!', 'info')
        return redirect(url_for('kelolagudang'))
    return redirect(url_for('kelolagudang'))

@app.route('/admin/gudang/delete/<int:id>', methods=['POST'])
@admin_required
def delete_item(id):
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('DELETE FROM gudang WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        flash('Data barang telah dihapus.', 'success')
        return redirect(url_for('kelolagudang'))
    return redirect(url_for('kelolagudang'))

if __name__ == '__main__':
    # Pastikan database ada sebelum aplikasi dijalankan
    if not os.path.exists(DATABASE):
        print(f"Database tidak ditemukan di '{DATABASE}'. Jalankan 'init_db.py' terlebih dahulu.")
    else:
        app.run(debug=True)