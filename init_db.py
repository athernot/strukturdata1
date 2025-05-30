# init_db.py

import sqlite3
import os
from werkzeug.security import generate_password_hash

# Nama file database
DB_FILE = 'gudang.db'

def initialize_database():
    """Membuat dan menginisialisasi database jika belum ada."""
    
    if os.path.exists(DB_FILE):
        print(f"Database '{DB_FILE}' sudah ada. Mengecek struktur tabel...")
    
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    print("1. Membuat tabel 'gudang' jika belum ada...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gudang (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_barang TEXT NOT NULL UNIQUE,
            nama_barang TEXT NOT NULL,
            deskripsi TEXT,
            gambar TEXT,
            tanggal DATE NOT NULL,
            jumlah INTEGER NOT NULL,
            harga INTEGER NOT NULL DEFAULT 150000
        )
    ''')

    print("2. Membuat tabel 'users' untuk autentikasi jika belum ada...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    ''')
    
    print("3. Membuat tabel 'laporan' untuk laporan jika belum ada...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS laporan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipe_laporan TEXT NOT NULL,
            judul_laporan TEXT NOT NULL,
            isi_laporan TEXT NOT NULL,
            pelapor TEXT NOT NULL,
            tanggal_lapor TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    print("NEW: Membuat tabel 'transaksi' untuk log barang...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transaksi (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_barang_gudang INTEGER NOT NULL,
            nama_barang TEXT NOT NULL,
            tipe TEXT NOT NULL,
            jumlah INTEGER NOT NULL,
            tanggal TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    print("NEW: Membuat tabel 'pesanan' untuk checkout...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pesanan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nomor_pesanan TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            nama_penerima TEXT NOT NULL,
            alamat_pengiriman TEXT NOT NULL,
            telepon TEXT NOT NULL,
            total_harga INTEGER NOT NULL,
            metode_pembayaran TEXT NOT NULL,
            status_pembayaran TEXT NOT NULL DEFAULT 'Belum Dibayar',
            tanggal_pesan TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    print("NEW: Membuat tabel 'detail_pesanan' untuk item dalam pesanan...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detail_pesanan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pesanan_id INTEGER NOT NULL,
            gudang_id INTEGER NOT NULL,
            nama_barang TEXT NOT NULL,
            jumlah INTEGER NOT NULL,
            harga_satuan INTEGER NOT NULL,
            FOREIGN KEY (pesanan_id) REFERENCES pesanan (id),
            FOREIGN KEY (gudang_id) REFERENCES gudang (id)
        )
    ''')

    print("4. Menambahkan data awal ke tabel 'gudang'...")
    initial_items = [
        ('BRG-001', 'Sepatu Lari Adidas', 'Sepatu lari yang ringan dan nyaman untuk performa maksimal.', 'https://images.pexels.com/photos/2529148/pexels-photo-2529148.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1', '2024-05-20', 100, 750000),
        ('BRG-002', 'Kaos Polos Katun', 'Kaos katun premium yang lembut dan sejuk dipakai sehari-hari.', 'https://images.pexels.com/photos/428338/pexels-photo-428338.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1', '2024-05-22', 250, 150000),
        ('BRG-003', 'Celana Jeans Levis', 'Celana jeans klasik dengan potongan modern dan bahan yang tahan lama.', 'https://images.pexels.com/photos/1598507/pexels-photo-1598507.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1', '2024-05-23', 75, 550000),
        ('BRG-004', 'Jam Tangan Casio', 'Jam tangan digital klasik yang fungsional dan bergaya retro.', 'https://images.pexels.com/photos/190819/pexels-photo-190819.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1', '2024-05-24', 50, 450000),
        ('BRG-005', 'Tas Ransel Eiger', 'Tas ransel kuat dan serbaguna untuk kegiatan outdoor maupun sehari-hari.', 'https://images.pexels.com/photos/1545403/pexels-photo-1545403.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1', '2024-05-25', 120, 400000),
        ('BRG-006', 'Kemeja Flanel', 'Kemeja flanel hangat dengan motif kotak-kotak yang timeless.', 'https://images.pexels.com/photos/3755706/pexels-photo-3755706.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1', '2024-05-26', 90, 250000)
    ]

    # Cek dan tambahkan kolom 'harga' jika belum ada
    try:
        cursor.execute("SELECT harga FROM gudang LIMIT 1")
    except sqlite3.OperationalError:
        print("   - Menambahkan kolom 'harga' ke tabel 'gudang'...")
        cursor.execute("ALTER TABLE gudang ADD COLUMN harga INTEGER NOT NULL DEFAULT 150000")

    # Update data yang ada untuk memastikan harga tidak NULL
    cursor.execute("UPDATE gudang SET harga = 150000 WHERE harga IS NULL")

    for item in initial_items:
        cursor.execute("INSERT OR IGNORE INTO gudang (id_barang, nama_barang, deskripsi, gambar, tanggal, jumlah, harga) VALUES (?, ?, ?, ?, ?, ?, ?)", item)


    print("5. Menambahkan user admin default...")
    try:
        hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
        cursor.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES (?, ?, ?)",
                       ('admin', hashed_password, 'admin'))
        print("   - User 'admin' berhasil dibuat atau sudah ada.")
    except sqlite3.IntegrityError:
        print("   - User 'admin' sudah ada, tidak ada perubahan.")
        pass

    connection.commit()
    connection.close()

    print("\nInisialisasi database selesai.")
    print(f"Database '{DB_FILE}' siap digunakan.")
    print("User default: username='admin', password='admin123'")

if __name__ == '__main__':
    initialize_database()