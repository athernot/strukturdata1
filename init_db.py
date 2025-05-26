# init_db.py

import sqlite3
import os
from werkzeug.security import generate_password_hash

# Nama file database
DB_FILE = 'gudang.db'

def initialize_database():
    """Membuat dan menginisialisasi database jika belum ada."""
    
    # Hapus file database lama jika ada, untuk memulai dari awal (opsional)
    if os.path.exists(DB_FILE):
        print(f"Database '{DB_FILE}' sudah ada. Menginisialisasi ulang...")
        # os.remove(DB_FILE) # Hapus komentar ini jika ingin selalu membuat database baru
    
    # Membuat koneksi ke file database.
    # Jika file belum ada, maka akan dibuat secara otomatis.
    connection = sqlite3.connect(DB_FILE)
    cursor = connection.cursor()

    print("1. Membuat tabel 'gudang'...")
    # Menggunakan TEXT untuk tipe data agar fleksibel
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gudang (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_barang TEXT NOT NULL UNIQUE,
            nama_barang TEXT NOT NULL,
            tanggal DATE NOT NULL,
            jumlah INTEGER NOT NULL
        )
    ''')

    print("2. Membuat tabel 'users' untuk autentikasi...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user'
        )
    ''')

    print("3. Menambahkan data awal ke tabel 'gudang'...")
    initial_items = [
        ('BRG-001', 'Sepatu Lari Adidas', '2024-05-20', 100),
        ('BRG-002', 'Kaos Polos Katun', '2024-05-22', 250),
        ('BRG-003', 'Celana Jeans Levis', '2024-05-23', 75),
    ]
    # Menggunakan INSERT OR IGNORE untuk menghindari error jika data sudah ada
    cursor.executemany("INSERT OR IGNORE INTO gudang (id_barang, nama_barang, tanggal, jumlah) VALUES (?, ?, ?, ?)", initial_items)

    print("4. Menambahkan user admin default...")
    # Kata sandi di-hash sebelum disimpan untuk keamanan
    try:
        hashed_password = generate_password_hash('admin123', method='pbkdf2:sha256')
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       ('admin', hashed_password, 'admin'))
        print("   - User 'admin' berhasil dibuat.")
    except sqlite3.IntegrityError:
        # Jika admin sudah ada, tidak perlu lakukan apa-apa
        print("   - User 'admin' sudah ada, tidak ada perubahan.")
        pass

    # Menyimpan perubahan (commit) dan menutup koneksi
    connection.commit()
    connection.close()

    print("\nInisialisasi database selesai.")
    print(f"Database '{DB_FILE}' siap digunakan.")
    print("User default: username='admin', password='admin123'")

if __name__ == '__main__':
    initialize_database()