# main.py

import os
import sqlite3
import uuid
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
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
    return render_template('user/index.html')

@app.route('/katalog')
def katalog():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM gudang WHERE jumlah > 0 ORDER BY tanggal DESC').fetchall()
    conn.close()
    return render_template('user/katalog.html', items=items)

@app.route('/kontak')
def kontak():
    return render_template('user/kontak.html')

# --- RUTE KERANJANG & CHECKOUT ---
@app.route('/cart/add/<int:item_id>', methods=['POST'])
@login_required
def add_to_cart(item_id):
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    item_id_str = str(item_id)
    
    # Ambil jumlah dari form, default 1
    quantity = int(request.form.get('quantity', 1))

    # Cek stok
    conn = get_db_connection()
    item = conn.execute('SELECT jumlah FROM gudang WHERE id = ?', (item_id,)).fetchone()
    conn.close()

    if not item:
        flash('Barang tidak ditemukan.', 'danger')
        return redirect(url_for('katalog'))
        
    current_quantity_in_cart = cart.get(item_id_str, 0)
    
    if (current_quantity_in_cart + quantity) > item['jumlah']:
        flash(f"Stok tidak mencukupi. Hanya tersedia {item['jumlah']} unit.", 'warning')
    else:
        cart[item_id_str] = current_quantity_in_cart + quantity
        flash(f"Barang berhasil ditambahkan ke keranjang!", 'success')

    session['cart'] = cart
    return redirect(request.referrer or url_for('katalog'))

@app.route('/cart')
@login_required
def cart():
    if 'cart' not in session or not session['cart']:
        return render_template('user/checkout.html', items_in_cart=[], total_price=0)

    cart = session['cart']
    item_ids = list(cart.keys())
    
    conn = get_db_connection()
    # Membuat placeholder untuk query IN
    placeholders = ','.join(['?'] * len(item_ids))
    query = f'SELECT * FROM gudang WHERE id IN ({placeholders})'
    db_items = conn.execute(query, item_ids).fetchall()
    conn.close()
    
    items_in_cart = []
    total_price = 0
    
    for item in db_items:
        item_id = str(item['id'])
        quantity = cart[item_id]
        
        # --- PERBAIKAN DIMULAI DI SINI ---
        # Cek apakah kolom 'harga' ada pada item. Jika tidak, anggap harganya 0.
        item_price = item['harga'] if 'harga' in item.keys() else 0
        
        subtotal = item_price * quantity
        # --- PERBAIKAN SELESAI ---

        total_price += subtotal
        
        items_in_cart.append({
            'id': item['id'],
            'nama_barang': item['nama_barang'],
            'gambar': item['gambar'],
            'harga': item_price, # Gunakan harga yang sudah divalidasi
            'quantity': quantity,
            'subtotal': subtotal
        })

    return render_template('user/checkout.html', items_in_cart=items_in_cart, total_price=total_price)

@app.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
    item_id = str(request.form.get('item_id'))
    quantity = int(request.form.get('quantity'))
    
    if 'cart' in session and item_id in session['cart']:
        if quantity > 0:
            # Cek stok
            conn = get_db_connection()
            item = conn.execute('SELECT jumlah FROM gudang WHERE id = ?', (item_id,)).fetchone()
            conn.close()

            if quantity > item['jumlah']:
                 flash(f"Stok tidak mencukupi. Hanya tersedia {item['jumlah']} unit.", 'warning')
            else:
                session['cart'][item_id] = quantity
                flash('Jumlah barang diperbarui.', 'success')
        else:
            # Hapus item jika jumlah 0 atau kurang
            session['cart'].pop(item_id, None)
            flash('Barang dihapus dari keranjang.', 'info')
        
        session.modified = True
    
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    item_id_str = str(item_id)
    if 'cart' in session and item_id_str in session['cart']:
        session['cart'].pop(item_id_str, None)
        session.modified = True
        flash('Barang berhasil dihapus dari keranjang.', 'success')
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    if 'cart' not in session or not session['cart']:
        flash('Keranjang Anda kosong.', 'warning')
        return redirect(url_for('cart'))

    # Ambil data dari form
    nama_penerima = request.form.get('nama_penerima')
    alamat_pengiriman = request.form.get('alamat_pengiriman')
    telepon = request.form.get('telepon')
    metode_pembayaran = request.form.get('metode_pembayaran')

    if not all([nama_penerima, alamat_pengiriman, telepon, metode_pembayaran]):
        flash('Harap lengkapi semua informasi pengiriman dan pembayaran.', 'danger')
        return redirect(url_for('cart'))

    # Proses item di keranjang
    cart = session['cart']
    item_ids = list(cart.keys())
    conn = get_db_connection()
    
    try:
        placeholders = ','.join(['?'] * len(item_ids))
        query = f'SELECT * FROM gudang WHERE id IN ({placeholders})'
        db_items = conn.execute(query, item_ids).fetchall()
        
        # --- PERBAIKAN DIMULAI DI SINI ---
        # Validasi: Cek jika ada barang di keranjang yang sudah tidak ada di database
        if len(db_items) != len(item_ids):
            flash('Beberapa barang di keranjang Anda sudah tidak tersedia dan telah kami hapus secara otomatis.', 'warning')
            
            # Dapatkan ID barang yang valid (masih ada di DB)
            found_ids = {str(item['id']) for item in db_items}
            
            # Buat ulang keranjang hanya dengan barang yang valid
            new_cart = {key: value for key, value in cart.items() if key in found_ids}
            session['cart'] = new_cart
            session.modified = True
            
            # Alihkan kembali ke halaman keranjang agar pengguna bisa melihat perubahannya
            return redirect(url_for('cart'))
        # --- PERBAIKAN SELESAI ---

        total_price = 0
        items_to_order = []

        for item in db_items:
            item_id = str(item['id'])
            quantity = cart[item_id]
            
            # Validasi stok
            if quantity > item['jumlah']:
                raise ValueError(f"Stok untuk {item['nama_barang']} tidak mencukupi.")
            
            subtotal = item['harga'] * quantity
            total_price += subtotal
            items_to_order.append({
                'gudang_id': item['id'],
                'nama_barang': item['nama_barang'],
                'jumlah': quantity,
                'harga_satuan': item['harga']
            })

        # Buat pesanan
        nomor_pesanan = f'INV-{uuid.uuid4().hex[:8].upper()}'
        
        # Insert ke tabel 'pesanan'
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO pesanan (nomor_pesanan, user_id, nama_penerima, alamat_pengiriman, telepon, total_harga, metode_pembayaran, status_pembayaran)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nomor_pesanan, session['user_id'], nama_penerima, alamat_pengiriman, telepon, total_price, metode_pembayaran, 'Lunas'))
        
        pesanan_id = cursor.lastrowid
        
        # Insert ke 'detail_pesanan' dan update stok 'gudang'
        for order_item in items_to_order:
            cursor.execute('''
                INSERT INTO detail_pesanan (pesanan_id, gudang_id, nama_barang, jumlah, harga_satuan)
                VALUES (?, ?, ?, ?, ?)
            ''', (pesanan_id, order_item['gudang_id'], order_item['nama_barang'], order_item['jumlah'], order_item['harga_satuan']))
            
            # Kurangi stok
            cursor.execute(
                'UPDATE gudang SET jumlah = jumlah - ? WHERE id = ?',
                (order_item['jumlah'], order_item['gudang_id'])
            )

        conn.commit()
        
        # Simpan nomor pesanan untuk halaman konfirmasi
        session['last_order_id'] = pesanan_id
        
        # Kosongkan keranjang
        session.pop('cart', None)
        
        flash('Pesanan berhasil dibuat!', 'success')
        return redirect(url_for('order_confirmation'))

    except ValueError as e:
        flash(str(e), 'danger')
        conn.rollback()
        return redirect(url_for('cart'))
    except Exception as e:
        flash(f'Terjadi kesalahan saat memproses pesanan: {e}', 'danger')
        conn.rollback()
        return redirect(url_for('cart'))
    finally:
        conn.close()

@app.route('/order-confirmation')
@login_required
def order_confirmation():
    last_order_id = session.get('last_order_id')
    if not last_order_id:
        return redirect(url_for('index'))

    conn = get_db_connection()
    pesanan = conn.execute('SELECT *, strftime("%d-%m-%Y %H:%M", tanggal_pesan) as tgl_formatted FROM pesanan WHERE id = ?', (last_order_id,)).fetchone()
    detail_pesanan = conn.execute('SELECT * FROM detail_pesanan WHERE pesanan_id = ?', (last_order_id,)).fetchall()
    conn.close()
    
    if not pesanan or pesanan['user_id'] != session['user_id']:
        flash('Pesanan tidak ditemukan.', 'danger')
        return redirect(url_for('index'))

    # Hapus dari session setelah ditampilkan
    session.pop('last_order_id', None)

    return render_template('user/order_confirmation.html', pesanan=pesanan, detail_pesanan=detail_pesanan)


# --- RUTE HALAMAN ADMIN ---
@app.route('/admin/home')
@login_required
def admin_home():
    conn = get_db_connection()
    
    # Menghitung Total Stok Barang
    total_items_query = conn.execute('SELECT SUM(jumlah) FROM gudang').fetchone()
    total_items = total_items_query[0] if total_items_query[0] is not None else 0

    # Menghitung Jumlah Jenis Barang
    unique_items_query = conn.execute('SELECT COUNT(id) FROM gudang').fetchone()
    unique_items = unique_items_query[0] if unique_items_query[0] is not None else 0
    
    # Menghitung Stok Kritis (contoh: stok < 50)
    KRITIS_THRESHOLD = 50
    stok_kritis_query = conn.execute('SELECT COUNT(id) FROM gudang WHERE jumlah < ?', (KRITIS_THRESHOLD,)).fetchone()
    stok_kritis = stok_kritis_query[0] if stok_kritis_query[0] is not None else 0

    # Menghitung total barang keluar dari tabel transaksi (contoh: 30 hari terakhir)
    barang_keluar_total_query = conn.execute("SELECT SUM(jumlah) FROM transaksi WHERE tipe = 'keluar' AND tanggal >= date('now', '-30 days')").fetchone()
    total_barang_keluar = barang_keluar_total_query[0] if barang_keluar_total_query[0] is not None else 0

    # Data untuk Grafik Tren (7 hari terakhir) - PERBAIKAN DI SINI
    barang_masuk_trend = conn.execute("SELECT strftime('%Y-%m-%d', tanggal) as tgl, SUM(jumlah) as total FROM transaksi WHERE tipe = 'masuk' AND tanggal >= date('now', '-7 days') GROUP BY tgl ORDER BY tgl ASC").fetchall()
    barang_keluar_trend = conn.execute("SELECT strftime('%Y-%m-%d', tanggal) as tgl, SUM(jumlah) as total FROM transaksi WHERE tipe = 'keluar' AND tanggal >= date('now', '-7 days') GROUP BY tgl ORDER BY tgl ASC").fetchall()
    conn.close()

    # Memproses data untuk grafik ApexCharts - PERBAIKAN DI SINI
    dates = sorted(list(set([row['tgl'] for row in barang_masuk_trend] + [row['tgl'] for row in barang_keluar_trend])))
    masuk_data_map = {row['tgl']: row['total'] for row in barang_masuk_trend}
    # Baris ini yang diperbaiki: menggunakan 'barang_keluar_trend'
    keluar_data_map = {row['tgl']: row['total'] for row in barang_keluar_trend}
    
    chart_data_masuk = [masuk_data_map.get(date, 0) for date in dates]
    chart_data_keluar = [keluar_data_map.get(date, 0) for date in dates]

    return render_template('admin/index.html', 
                           total_items=total_items,
                           unique_items=unique_items,
                           barang_keluar=total_barang_keluar,
                           stok_kritis=stok_kritis,
                           chart_labels=dates,
                           chart_data_masuk=chart_data_masuk,
                           chart_data_keluar=chart_data_keluar)

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
    # ... (mengambil form data) ...

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Masukkan ke tabel gudang
        cursor.execute('INSERT INTO gudang (id_barang, nama_barang, tanggal, jumlah, deskripsi, gambar, harga) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (request.form['id_barang'], request.form['nama_barang'], request.form['tanggal'], int(request.form['jumlah']), request.form.get('deskripsi', ''), request.form.get('gambar', ''), int(request.form['harga'])))
        
        new_item_id = cursor.lastrowid
        
        # Catat di tabel transaksi sebagai 'masuk'
        cursor.execute('INSERT INTO transaksi (id_barang_gudang, nama_barang, tipe, jumlah) VALUES (?, ?, ?, ?)',
                     (new_item_id, request.form['nama_barang'], 'masuk', int(request.form['jumlah'])))

        conn.commit()
        flash('Barang berhasil ditambahkan!', 'success')
    except sqlite3.IntegrityError:
        flash(f"ID Barang '{request.form['id_barang']}' sudah ada. Gunakan ID lain.", 'danger')
    except (ValueError, TypeError):
        flash('Jumlah dan Harga harus berupa angka.', 'danger')
    finally:
        conn.close()
    return redirect(url_for('kelola_gudang'))

@app.route('/admin/gudang/keluar', methods=['POST'])
@admin_required
def barang_keluar():
    id_gudang = request.form.get('id_gudang')
    try:
        jumlah_keluar = int(request.form.get('jumlah_keluar'))
        if jumlah_keluar <= 0:
            raise ValueError("Jumlah keluar harus positif")
    except (ValueError, TypeError):
        flash('Jumlah harus berupa angka positif.', 'danger')
        return redirect(url_for('kelola_gudang'))

    conn = get_db_connection()
    item = conn.execute('SELECT * FROM gudang WHERE id = ?', (id_gudang,)).fetchone()

    if not item or item['jumlah'] < jumlah_keluar:
        flash('Stok tidak mencukupi atau barang tidak ditemukan.', 'danger')
        conn.close()
        return redirect(url_for('kelola_gudang'))

    # Update stok di tabel gudang
    stok_baru = item['jumlah'] - jumlah_keluar
    conn.execute('UPDATE gudang SET jumlah = ? WHERE id = ?', (stok_baru, id_gudang))
    
    # Catat di tabel transaksi
    conn.execute('INSERT INTO transaksi (id_barang_gudang, nama_barang, tipe, jumlah) VALUES (?, ?, ?, ?)',
                 (id_gudang, item['nama_barang'], 'keluar', jumlah_keluar))
    
    conn.commit()
    conn.close()
    
    flash(f"{jumlah_keluar} unit {item['nama_barang']} telah dikeluarkan dari gudang.", 'success')
    return redirect(url_for('kelola_gudang'))

@app.route('/admin/gudang/edit/<int:id>', methods=['POST'])
@admin_required
def edit_item(id):
    nama_barang_form = request.form['nama_barang']
    tanggal_form = request.form['tanggal']
    jumlah_form = request.form['jumlah']
    deskripsi_form = request.form.get('deskripsi', '')
    gambar_form = request.form.get('gambar', '')
    harga_form = request.form.get('harga', 0)

    conn = get_db_connection()
    try:
        conn.execute('UPDATE gudang SET nama_barang = ?, tanggal = ?, jumlah = ?, deskripsi = ?, gambar = ?, harga = ? WHERE id = ?',
                     (nama_barang_form, tanggal_form, int(jumlah_form), deskripsi_form, gambar_form, int(harga_form), id))
        conn.commit()
        flash('Data barang berhasil diperbarui!', 'info')
    except (ValueError, TypeError):
        flash('Jumlah dan Harga harus berupa angka.', 'danger')
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