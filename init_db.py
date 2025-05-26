# init_db.py

import sqlite3

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

# 2. Data awal yang akan dimasukkan
initial_items = [
    ('BRG-001', 'Sepatu Lari Adidas', '2024-05-20', 100),
    ('BRG-002', 'Kaos Polos Katun', '2024-05-22', 250),
    ('BRG-003', 'Celana Jeans Levis', '2024-05-23', 75),
]

# 3. Memasukkan data awal ke dalam tabel
# Menggunakan 'IGNORE' untuk menghindari error jika id_barang sudah ada
cursor.executemany("INSERT OR IGNORE INTO gudang (id_barang, nama_barang, tanggal, jumlah) VALUES (?, ?, ?, ?)", initial_items)

# 4. Menyimpan perubahan (commit) dan menutup koneksi
connection.commit()
connection.close()

print("Database 'gudang.db' berhasil diinisialisasi dengan data awal.")