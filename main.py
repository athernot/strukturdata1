# main.py

import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

# --- KONFIGURASI APLIKASI ---
app = Flask(__name__)
# Kunci rahasia diperlukan untuk sesi dan pesan flash.
# Ganti dengan kunci yang lebih aman di lingkungan produksi.
app.secret_key = 'super_secret_key_that_should_be_changed'

# Lokasi database
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gudang.db')

def get_db_connection():
    """Membuat koneksi ke database SQLite."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Memungkinkan akses kolom berdasarkan nama
    return conn

# --- DECORATOR OTENTIKASI ---
def login_required(f):
    """Decorator untuk memastikan user sudah login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Anda harus login untuk mengakses halaman ini.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator untuk memastikan user adalah admin."""
    @wraps(f)
    @login_required  # Admin juga harus login
    def decorated_function(*args, **kwargs):
        if session.get('user_role') != 'admin':
            flash('Hanya admin yang dapat mengakses halaman ini.', 'danger')
            return redirect(url_for('admin_home'))  # Arahkan ke dashboard admin
        return f(*args, **kwargs)
    return decorated_function

# --- RUTE OTENTIKASI ---
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
            flash(f"Selamat datang kembali, {user['username']}!", 'success')
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_home'))
            else:
                return redirect(url_for('index')) # Arahkan user biasa
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
@login_required
def logout():
    session.clear()
    flash('Anda telah berhasil logout.', 'info')
    return redirect(url_for('login'))

# --- RUTE HALAMAN PENGGUNA (UMUM) ---
@app.route('/')
def index():
    return render_template('user/index.html')

@app.route('/tentang')
def tentang():
    return render_template('user/tentang.html')

@app.route('/kontak')
def kontak():
    return render_template('user/kontak.html')

# --- RUTE HALAMAN ADMIN (TERLINDUNGI) ---
@app.route('/admin/home')
@login_required
def admin_home():
    # Periksa role untuk memastikan hanya admin atau user yang login bisa masuk
    # Konten halaman bisa disesuaikan berdasarkan role jika perlu
    return render_template('admin/index.html')

@app.route('/admin/kelola-gudang')
@admin_required
def kelola_gudang():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM gudang ORDER BY tanggal DESC, id DESC').fetchall()
    conn.close()
    return render_template('admin/gudang.html', items=items)

@app.route('/admin/laporan')
@admin_required
def laporan():
    return render_template('admin/laporan.html')

# --- OPERASI CRUD GUDANG (HANYA ADMIN) ---
@app.route('/admin/gudang/add', methods=['POST'])
@admin_required
def add_item():
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
        flash(f"ID Barang '{id_barang}' sudah ada. Gunakan ID lain.", 'danger')
    except (ValueError, TypeError):
        flash('Jumlah harus berupa angka.', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('kelola_gudang'))

@app.route('/admin/gudang/edit/<int:id>', methods=['POST'])
@admin_required
def edit_item(id):
    id_barang_form = request.form['id_barang']
    nama_barang_form = request.form['nama_barang']
    tanggal_form = request.form['tanggal']
    jumlah_form = request.form['jumlah']
    
    conn = get_db_connection()
    try:
        conn.execute('UPDATE gudang SET id_barang = ?, nama_barang = ?, tanggal = ?, jumlah = ? WHERE id = ?',
                     (id_barang_form, nama_barang_form, tanggal_form, int(jumlah_form), id))
        conn.commit()
        flash('Data barang berhasil diperbarui!', 'info')
    except sqlite3.IntegrityError:
        flash(f"ID Barang '{id_barang_form}' sudah digunakan oleh item lain.", 'danger')
    except (ValueError, TypeError):
        flash('Jumlah harus berupa angka.', 'danger')
    finally:
        conn.close()

    return redirect(url_for('kelola_gudang'))

@app.route('/admin/gudang/delete/<int:id>', methods=['POST'])
@admin_required
def delete_item(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM gudang WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Data barang telah dihapus.', 'success')
    return redirect(url_for('kelola_gudang'))

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    # Pastikan database ada sebelum aplikasi dijalankan
    if not os.path.exists(DATABASE):
        print(f"Database tidak ditemukan di '{DATABASE}'.")
        print("Menjalankan 'init_db.py' untuk membuat database baru...")
        # Secara otomatis memanggil fungsi inisialisasi jika file tidak ada
        import init_db
        init_db.initialize_database()
    
    # Menjalankan aplikasi dalam mode debug
    app.run(debug=True)