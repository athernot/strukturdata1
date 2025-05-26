# main.py

import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

# --- KONFIGURASI APLIKASI ---
app = Flask(__name__)
app.secret_key = 'super_secret_key_that_should_be_changed'
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gudang.db')

def get_db_connection():
    """Membuat koneksi ke database SQLite."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# --- DECORATOR OTENTIKASI ---
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
    @login_required
    def decorated_function(*args, **kwargs):
        if session.get('user_role') != 'admin':
            flash('Hanya admin yang dapat mengakses halaman ini.', 'danger')
            return redirect(url_for('admin_home'))
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
@login_required
def logout():
    session.clear()
    flash('Anda telah berhasil logout.', 'info')
    return redirect(url_for('login'))

# --- RUTE HALAMAN PENGGUNA (UMUM) ---
@app.route('/')
def index():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM gudang ORDER BY tanggal DESC LIMIT 6').fetchall()
    conn.close()
    return render_template('user/index.html', items=items)

@app.route('/tentang')
def tentang():
    return render_template('user/tentang.html')

@app.route('/kontak')
def kontak():
    return render_template('user/kontak.html')

# --- RUTE HALAMAN ADMIN ---
@app.route('/admin/home')
@login_required
def admin_home():
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
    deskripsi = request.form.get('deskripsi', '') 
    gambar = request.form.get('gambar', '')

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO gudang (id_barang, nama_barang, tanggal, jumlah, deskripsi, gambar) VALUES (?, ?, ?, ?, ?, ?)',
                     (id_barang, nama_barang, tanggal, int(jumlah), deskripsi, gambar))
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
    nama_barang_form = request.form['nama_barang']
    tanggal_form = request.form['tanggal']
    jumlah_form = request.form['jumlah']
    deskripsi_form = request.form.get('deskripsi', '')
    gambar_form = request.form.get('gambar', '')

    conn = get_db_connection()
    try:
        conn.execute('UPDATE gudang SET nama_barang = ?, tanggal = ?, jumlah = ?, deskripsi = ?, gambar = ? WHERE id = ?',
                     (nama_barang_form, tanggal_form, int(jumlah_form), deskripsi_form, gambar_form, id))
        conn.commit()
        flash('Data barang berhasil diperbarui!', 'info')
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

# --- OPERASI LAPORAN (HANYA ADMIN) ---
@app.route('/admin/laporan/submit', methods=['POST'])
@admin_required
def submit_laporan():
    tipe_laporan = request.form.get('tipe_laporan')
    judul_laporan = request.form.get('judul_laporan')
    isi_laporan = request.form.get('isi_laporan')
    pelapor = session.get('username', 'admin')

    if not all([tipe_laporan, judul_laporan, isi_laporan]):
        flash('Semua field harus diisi.', 'danger')
        return redirect(url_for('laporan'))

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO laporan (tipe_laporan, judul_laporan, isi_laporan, pelapor) VALUES (?, ?, ?, ?)',
                     (tipe_laporan, judul_laporan, isi_laporan, pelapor))
        conn.commit()
        flash('Laporan berhasil dikirim!', 'success')
    except Exception as e:
        flash(f'Terjadi kesalahan saat mengirim laporan: {e}', 'danger')
    finally:
        conn.close()
    return redirect(url_for('preview_laporan'))

@app.route('/admin/laporan/preview')
@admin_required
def preview_laporan():
    conn = get_db_connection()
    all_reports = conn.execute('SELECT *, strftime("%d-%m-%Y %H:%M", tanggal_lapor) as tgl_formatted FROM laporan ORDER BY tanggal_lapor DESC').fetchall()
    conn.close()
    return render_template('admin/preview.html', reports=all_reports)

@app.route('/admin/laporan/delete/<int:id>', methods=['POST'])
@admin_required
def delete_laporan(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM laporan WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Laporan telah dihapus.', 'success')
    return redirect(url_for('preview_laporan'))

# --- MAIN EXECUTION ---
if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        print(f"Database tidak ditemukan di '{DATABASE}'. Menjalankan 'init_db.py'...")
        import init_db
        init_db.initialize_database()
    app.run(debug=True)