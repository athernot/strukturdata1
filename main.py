from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# User Routes
@app.route('/')
def index():
    return render_template('user/index.html')

@app.route('/tentang')
def tentang():
    return render_template('user/tentang.html')

@app.route('/kontak')
def kontak():
    return render_template('user/kontak.html')

# Dummy data - nantinya ini akan diganti dengan data dari database Anda
dummy_items = [
    {'id': 1, 'id_barang': 'BRG-001', 'nama_barang': 'Sepatu Lari Adidas', 'tanggal': '2024-05-20', 'jumlah': 100},
    {'id': 2, 'id_barang': 'BRG-002', 'nama_barang': 'Kaos Polos Katun', 'tanggal': '2024-05-22', 'jumlah': 250},
    {'id': 3, 'id_barang': 'BRG-003', 'nama_barang': 'Celana Jeans Levis', 'tanggal': '2024-05-23', 'jumlah': 75},
]

# Admin Routes

@app.route('/admin/home')
def admin_home(): # Mengganti nama fungsi agar unik jika 'home' sudah ada
    return render_template('admin/index.html')

@app.route('/admin/admin-kelola-barang')
def kelolabarang():
    # Halaman ini mungkin memerlukan logikanya sendiri atau data dari database
    return render_template('admin/barang.html')

@app.route('/admin/admin-kelola-gudang')
def kelolagudang():
    """
    Fungsi ini menampilkan halaman utama gudang.
    Mengambil data (saat ini dummy_items) dan mengirimkannya ke template.
    """
    items = dummy_items 
    return render_template('admin/gudang.html', items=items)

@app.route('/admin/gudang/add', methods=['POST'])
def add_item():
    """
    Endpoint ini menangani penambahan data barang baru ke gudang.
    """
    if request.method == 'POST':
        id_barang = request.form.get('id_barang')
        nama_barang = request.form.get('nama_barang')
        tanggal = request.form.get('tanggal')
        jumlah = request.form.get('jumlah')

        # Untuk debugging, Anda bisa print data yang diterima
        print(f"Adding new item: ID Barang={id_barang}, Nama={nama_barang}, Tanggal={tanggal}, Jumlah={jumlah}")

        # DATABASE INTEGRATION: 
        # Di sini Anda akan menambahkan logika untuk menyimpan data baru ke database.
        # Contoh:
        # new_item_id = len(dummy_items) + 1 # Hasilkan ID baru (sementara)
        # dummy_items.append({'id': new_item_id, 'id_barang': id_barang, 'nama_barang': nama_barang, 'tanggal': tanggal, 'jumlah': int(jumlah)})
        # print("Item added to dummy_items:", dummy_items[-1])
        
        # Setelah data disimpan, redirect kembali ke halaman kelola gudang
        return redirect(url_for('kelolagudang'))
    # Jika bukan POST (meskipun route ini hanya untuk POST), redirect saja
    return redirect(url_for('kelolagudang'))


@app.route('/admin/gudang/edit/<int:id>', methods=['POST'])
def edit_item(id):
    """
    Endpoint ini menangani pembaruan data barang yang sudah ada di gudang.
    """
    if request.method == 'POST':
        item_id_to_edit = id
        id_barang_form = request.form.get('id_barang')
        nama_barang_form = request.form.get('nama_barang')
        tanggal_form = request.form.get('tanggal')
        jumlah_form = request.form.get('jumlah')
        
        print(f"Editing item ID {item_id_to_edit}: ID Barang={id_barang_form}, Nama={nama_barang_form}, Tanggal={tanggal_form}, Jumlah={jumlah_form}")

        # DATABASE INTEGRATION:
        # Di sini Anda akan menambahkan logika untuk memperbarui data di database berdasarkan 'item_id_to_edit'.
        # Contoh dengan dummy_items:
        # for item in dummy_items:
        #     if item['id'] == item_id_to_edit:
        #         item['id_barang'] = id_barang_form
        #         item['nama_barang'] = nama_barang_form
        #         item['tanggal'] = tanggal_form
        #         item['jumlah'] = int(jumlah_form)
        #         print("Item updated in dummy_items:", item)
        #         break
        
        return redirect(url_for('kelolagudang'))
    return redirect(url_for('kelolagudang'))

@app.route('/admin/gudang/delete/<int:id>', methods=['POST'])
def delete_item(id):
    """
    Endpoint ini menangani penghapusan data barang dari gudang.
    """
    if request.method == 'POST':
        item_id_to_delete = id
        print(f"Deleting item ID {item_id_to_delete}")

        # DATABASE INTEGRATION:
        # Di sini Anda akan menambahkan logika untuk menghapus data dari database berdasarkan 'item_id_to_delete'.
        # Contoh dengan dummy_items:
        # global dummy_items # Jika Anda memodifikasi list global
        # dummy_items = [item for item in dummy_items if item['id'] != item_id_to_delete]
        # print(f"Item with ID {item_id_to_delete} removed from dummy_items.")
        
        return redirect(url_for('kelolagudang'))
    return redirect(url_for('kelolagudang'))


if __name__ == '__main__':
    app.run(debug=True)
