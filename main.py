from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('user/index.html')
@app.route('/tentang')
def tentang():
    return render_template('user/tentang.html')

@app.route('/kontak')
def kontak():
    return render_template('user/kontak.html')


#  admin

@app.route('/admin/home')
def home():
    return render_template('admin/index.html')

@app.route('/admin/admin-kelola-barang')
def kelolabarang():
    return render_template('admin/barang.html')

@app.route('/admin/admin-kelola-gudang')
def kelolagudang():
    return render_template('admin/gudang.html')

@app.route('/authors')
def authors():
    authors = [
        {
            'id': 1,
            'nama_barang': 'Sepatu',
            'tanggal': '2023-10-01',
            'jumlah': '10',
            'tersedia': True,
            'avatar': '1.jpg'
        },
    ]
    return render_template('authors.html', authors=authors)


if __name__ == '__main__':
    app.run(debug=True)
