# init_db.py

import sqlite3
from werkzeug.security import generate_password_hash

# Membuat koneksi ke file database.
# Jika file belum ada, maka akan dibuat secara otomatis.
connection = sqlite3.connect('gudang.db')
cursor = connection.cursor()

# 1. Membuat tabel 'gudang'
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

# 2. [BARU] Membuat tabel 'users' untuk autentikasi
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user'
    )
''')

# 3. Data awal yang akan dimasukkan ke tabel 'gudang'
initial_items = [
    ('BRG-001', 'Sepatu Lari Adidas', '2024-05-20', 100),
    ('BRG-002', 'Kaos Polos Katun', '2024-05-22', 250),
    ('BRG-003', 'Celana Jeans Levis', '2024-05-23', 75),
]

# 4. Memasukkan data awal ke dalam tabel 'gudang'
cursor.executemany("INSERT OR IGNORE INTO gudang (id_barang, nama_barang, tanggal, jumlah) VALUES (?, ?, ?, ?)", initial_items)

# 5. [BARU] Menambahkan user admin default
# Kata sandi di-hash sebelum disimpan untuk keamanan
try:
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                   ('admin', generate_password_hash('admin123', method='pbkdf2:sha256'), 'admin'))
except sqlite3.IntegrityError:
    # Jika admin sudah ada, tidak perlu lakukan apa-apa
    pass

# 6. Menyimpan perubahan (commit) dan menutup koneksi
connection.commit()
connection.close()

print("Database 'gudang.db' berhasil diinisialisasi dengan tabel 'gudang' dan 'users'.")
print("User default: username='admin', password='admin123'")