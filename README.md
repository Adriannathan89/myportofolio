# Portfolio Website

### About Project
project ini merupakan project portfolio yang akan berisi seluruh pengalaman dan hasil pekerjaan saya. dan project ini juga berafiliasi dengan mata kuliah Pemrograman berbasis Platform Fakultas Ilmu Komputer Universitas Indonesia

### Identity
Name: Adrian Nathanael Setiawan

NPM: 2506591053

Class: PBP E

Aplikasi ini menyajikan profil, daftar project, dan pengalaman kerja/organisasi dalam satu halaman (single page), yang dirender oleh Django lewat template HTML alih-alih file HTML statis biasa. Konten halaman dibagi ke beberapa `<section>` semantik:

- **Profile (`#profile`)** — perkenalan diri: nama, kicker/judul singkat, bio, meta info, tautan sosial media, dan foto profil.
- **Projects (`#projects`)** — daftar project yang pernah dikerjakan, ditampilkan dalam bentuk card berisi judul, deskripsi, tags teknologi, dan tautan (GitHub/npm).
- **Experience (`#experience`)** — daftar pengalaman kerja/organisasi dalam bentuk card, lengkap dengan deskripsi dan poin-poin highlight.

### Tech Stack

- **Backend:** Django
- **Server produksi:** Gunicorn
- **Static files:** WhiteNoise
- **Database:** PostgreSQL (produksi) / SQLite (development lokal)
- **Environment variables:** python-dotenv

### Struktur Project

```
.
├── myportofolio/          # Django project package
│   ├── settings.py        # Konfigurasi project (DB, static files, apps, dll)
│   ├── urls.py             # Routing URL
│   ├── views.py            # View untuk landing page
│   ├── wsgi.py / asgi.py
├── templates/
│   └── index.html          # Template halaman utama (profile, projects, experience)
├── static/
│   ├── css/style.css       # Seluruh styling (layout, warna, responsive, hover effect)
│   └── img/                 # Aset gambar (foto profil, ikon GitHub/npm)
├── manage.py
├── requirements.txt
└── db.sqlite3               # Database default untuk development lokal

## Cara Menjalankan Secara Lokal

1. Clone repository dan masuk ke foldernya:
   ```bash
   git clone https://github.com/Adriannathan89/myportofolio.git
   cd myportofolio
   ```

2. Buat virtual environment lalu install dependencies:
   ```bash
   python -m venv env
   source env/bin/activate   # Windows: env\Scripts\activate
   pip install -r requirements.txt
   ```

3. Jalankan migrasi database (memakai SQLite secara default saat `PRODUCTION` tidak di-set):
   ```bash
   python manage.py migrate
   ```

4. Jalankan development server:
   ```bash
   python manage.py runserver
   ```

5. Buka `http://127.0.0.1:8000` di browser.

### Menjalankan dengan konfigurasi produksi (PostgreSQL)

Buat file `.env` berisi variabel berikut sebelum menjalankan dengan `PRODUCTION=True`:

```
PRODUCTION=True
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
DB_HOST=...
DB_PORT=...
SCHEMA=public
```

### Deployment

Aplikasi ini dideploy di domain PWS (Pacil Web Service) Fasilkom UI: <a href="adrian-nathanael-portfolio.pws.cs.ui.ac.id">Akses Disini</a>.

### Assignment 1
1. Ya saya menggunakan beberapa element semantik HTML5 seperti `<header>`, `<main>`, `<section>`, `<footer>`, `<ul>`, dan `<li>`. Penggunaan elemen semantic ini membantu dalam beberapa hal:

- **Struktur dokumen lebih jelas** — browser maupun screen reader dapat "membaca" hierarki halaman tanpa harus menebak dari nama class saja, dan tiap `<section>` punya `id` yang juga dipakai untuk anchor navigasi (`#profile`, `#projects`, `#experience`).
- **Aksesibilitas lebih baik** — pengguna teknologi assistive bisa langsung melompat ke bagian tertentu dari halaman.
- **SEO lebih baik** — search engine dapat lebih mudah mengenali bagian penting dari halaman, seperti konten utama vs navigasi.
- **CSS lebih terorganisir** — karena tiap bagian sudah punya batas elemen yang jelas, styling per section (hero, projects, experience) jadi lebih mudah dipisahkan dan di-maintain, meskipun halaman dirender lewat Django template.

2. Tantangan terbesar adalah:

* ketika membuat responsive dari card untuk project dan juga card experience karena di mode dekstop card ini tersusun secara horizontal dan ketika masuk ke mode mobile, designnya akan kurang proporsional jika memaksakan dibuat horizontal, maka akhirnya saya memutuskan untuk membuat designnya menjadi veritikal saat di mode mobile. 

* Tantangan lain ada pada bagian project card dan experience card yang di desktop menggunakan lebar sebagian (multi-kolom), tapi di mobile perlu diubah menjadi full width (1 kolom) agar konten tidak terlalu sempit. Ukuran font judul dan deskripsi juga perlu diperkecil di layar kecil agar proporsional.

* Nama dan bio dianggap paling penting untuk dibaca pertama sehingga design ini harus menjadi prioritas dalam membuat pengunjung nyaman, disusul foto sebagai elemen visual, baru detail meta. Breakpoint `600px` dipilih sebagai titik ubah layout karena di ukuran tersebut layout multi-kolom mulai terasa sempit dan sulit dibaca dengan nyaman.

3. Meskipun proyek ini sudah berbasis Django (bukan static HTML biasa), saat ini `landing_page` hanya melakukan `render(request, 'index.html')` tanpa mengambil data dari database — seluruh konten (nama, bio, daftar project, daftar experience) masih ditulis langsung di template. Ini membawa beberapa limitasi yang sama seperti static website:

- Menambah atau mengubah data project maupun pengalaman kerja masih harus dengan mengedit langsung file `templates/index.html`, belum memanfaatkan model dan database yang sudah tersedia di Django.
- Belum ada form kontak yang benar-benar terhubung ke backend untuk menyimpan atau mengirim pesan dari pengunjung.
- Belum ada autentikasi/admin panel yang dipakai untuk mengelola konten portofolio seperti untuk melihat metric pengunjung

Berdasarkan limitasi tersebut, fungsi dinamis yang paling ingin ditambahkan di iterasi berikutnya adalah:

1. **Model Django untuk Project dan Experience** — memindahkan data project dan pengalaman kerja dari hardcoded HTML ke model database, sehingga bisa ditambah/diubah lewat Django Admin tanpa mengedit kode.
2. **Form kontak fungsional** — memanfaatkan Django Forms dan `MAILERS`/email backend yang sudah dikonfigurasi untuk benar-benar mengirim pesan dari pengunjung ke pemilik portofolio.
3. **Autentikasi sederhana untuk halaman admin/CMS pribadi** — memanfaatkan `django.contrib.auth` untuk membuat halaman khusus mengelola konten portofolio (seperti metric pengunjung) secara aman.


### AI Disclosure
* Saat menngerjakan project ini saya menggunakan AI web based untuk membantu saya dalam melakukan dokumentasi project saya. Saya memberikan AI tugas untuk membuat penjelasan tentang tech stack, project structure, dan cara untuk menjalankan project ini. Hasil dari AI ini saya review kembali dan pastikan bahwa langkah-langkah yang di tulis AI sudah sesuai. 

* Selain itu, saya juga menggunakan AI Copilot untuk membatu saya dalam menulis kode, tentunya karena AI ini memeberikan suggestion dari line dimana saya sedang bekerja, otomatis saya langsung mereview inline suggestion yang diberikan oleh AI copilot ini. 