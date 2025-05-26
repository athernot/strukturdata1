# main.py

from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

app = Flask(__name__)

# Lokasi database
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gudang.db')

def get_db_connection():
    """Membuat koneksi ke database SQLite."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Ini memungkinkan kita mengakses kolom berdasarkan nama
    return conn

# --- User Routes (Tidak ada perubahan) ---
@app.route('/')
def index():
    return render_template('user/index.html')

@app.route('/tentang')
def tentang():
    return render_template('user/tentang.html')

@app.route('/kontak')
def kontak():
    return render_template('user/kontak.html')

# --- Admin Routes (Dimodifikasi untuk Database) ---

@app.route('/admin/home')
def admin_home():
    return render_template('admin/index.html')

@app.route('/admin/admin-kelola-barang')
def kelolabarang():
    return render_template('admin/barang.html')

@app.route('/admin/admin-kelola-gudang')
def kelolagudang():
    """
    [MODIFIED] Mengambil data dari database SQLite dan menampilkannya.
    """
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM gudang ORDER BY tanggal DESC').fetchall()
    conn.close()
    return render_template('admin/gudang.html', items=items)

@app.route('/admin/admin-laporan')
def laporan():
    return render_template('admin/laporan.html')

@app.route('/admin/gudang/add', methods=['POST'])
def add_item():
    """
    [MODIFIED] Menambahkan data barang baru ke database.
    """
    if request.method == 'POST':
        id_barang = request.form['id_barang']
        nama_barang = request.form['nama_barang']
        tanggal = request.form['tanggal']
        jumlah = request.form['jumlah']

        conn = get_db_connection()
        conn.execute('INSERT INTO gudang (id_barang, nama_barang, tanggal, jumlah) VALUES (?, ?, ?, ?)',
                     (id_barang, nama_barang, tanggal, int(jumlah)))
        conn.commit()
        conn.close()
        
        return redirect(url_for('kelolagudang'))
    return redirect(url_for('kelolagudang'))

@app.route('/admin/gudang/edit/<int:id>', methods=['POST'])
def edit_item(id):
    """
    [MODIFIED] Memperbarui data barang di database berdasarkan ID.
    """
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

        return redirect(url_for('kelolagudang'))
    return redirect(url_for('kelolagudang'))

@app.route('/admin/gudang/delete/<int:id>', methods=['POST'])
def delete_item(id):
    """
    [MODIFIED] Menghapus data barang dari database berdasarkan ID.
    """
    if request.method == 'POST':
        conn = get_db_connection()
        conn.execute('DELETE FROM gudang WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        
        return redirect(url_for('kelolagudang'))
    return redirect(url_for('kelolagudang'))

if __name__ == '__main__':
    # Pastikan database ada sebelum aplikasi dijalankan
    if not os.path.exists(DATABASE):
        print(f"Database tidak ditemukan di '{DATABASE}'. Jalankan 'init_db.py' terlebih dahulu.")
    else:
        app.run(debug=True)