# Portfolio Website

### About Project

Project ini merupakan website portfolio pribadi Adrian Nathanael Setiawan yang dibuat untuk mata kuliah Pemrograman Berbasis Platform, Fakultas Ilmu Komputer, Universitas Indonesia.

### Identity

Name: Adrian Nathanael Setiawan

NPM: 2506591053

Class: PBP E

Website ini menggunakan Django untuk merender halaman portfolio. Halaman utama menampilkan profile dan selected projects, sedangkan data experience dan award sudah disimpan di database dan dirender melalui halaman terpisah:

- **Profile (`/`)** — nama, bio, program studi, NPM, foto profil, dan tautan sosial media.
- **Projects (`/#projects`)** — project yang ditampilkan sebagai card berisi deskripsi, tags teknologi, serta tautan GitHub atau npm.
- **Experience (`/experience/`)** — data pengalaman dari model `Experience`, termasuk kategori, periode, thumbnail, deskripsi, dan key features.
- **Awards (`/award/`)** — data penghargaan dari model `Award`, termasuk judul, tanggal diterima, thumbnail sertifikat, deskripsi, dan issuer.

### Tech Stack

- **Backend:** Python dan Django 5.0
- **Template dan styling:** Django Templates, HTML, dan CSS responsive
- **Database:** SQLite untuk development lokal / PostgreSQL untuk production
- **Production server:** Gunicorn
- **Static files:** WhiteNoise
- **Environment variables:** python-dotenv
- **CI/CD:** GitHub Actions untuk menjalankan test pada pull request dan deploy ke PWS saat push ke branch `main`

### Model dan Data

Data portfolio yang bersifat dinamis berada di aplikasi `main`:

- `Experience` menyimpan `title`, `description`, `category`, `thumbnail`, `keyfeatures`, `start_at`, dan `ended_at`.
- `Award` menyimpan `title`, `description`, `thumbnail`, `issuer`, dan `date_received`.
- Migrasi database berada di `main/migrations/`.
- Data awal dapat dibuat atau diperbarui secara idempotent menggunakan script di folder `scripts/`.

Jalankan seed data setelah migrasi:

```bash
./scripts/seed_experience.sh
./scripts/seed_award.sh
```

Kedua script menggunakan interpreter `python` secara default. Interpreter dapat diganti melalui environment variable `PYTHON_BIN`, contohnya `PYTHON_BIN=python3 ./scripts/seed_award.sh`.

### Struktur Project

```
.
├── main/                         # Django app untuk portfolio
│   ├── models.py                 # Model Experience dan Award
│   ├── views.py                  # View profile, experience, dan award
│   ├── urls.py                   # Routing halaman portfolio
│   ├── admin.py                  # Konfigurasi Django admin
│   ├── test.py                   # Test aplikasi
│   └── migrations/               # Migrasi database
├── myportofolio/                 # Django project package
│   ├── settings.py               # Konfigurasi database dan static files
│   ├── urls.py                   # Root URL configuration
│   └── wsgi.py / asgi.py         # Entry point deployment
├── templates/
│   ├── index.html                # Profile dan selected projects
│   ├── experience.html            # Halaman experience dari database
│   └── award.html                 # Halaman award dari database
├── static/
│   ├── css/style.css              # Styling, layout, responsive, dan hover effect
│   └── img/                       # Foto profil, ikon project, dan thumbnail award
├── scripts/
│   ├── seed_experience.sh         # Seed/update data experience
│   └── seed_award.sh              # Seed/update data award
├── .github/workflows/             # Konfigurasi CI dan CD GitHub Actions
├── manage.py
├── requirements.txt
└── db.sqlite3                     # Database development lokal
```

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

3. Jalankan migrasi database. SQLite digunakan secara default saat `PRODUCTION` tidak di-set:

   ```bash
   python manage.py migrate
   ```

4. Masukkan data experience dan award:

   ```bash
   ./scripts/seed_experience.sh
   ./scripts/seed_award.sh
   ```

5. Jalankan development server:

   ```bash
   python manage.py runserver
   ```

6. Buka halaman berikut di browser:

   - `http://127.0.0.1:8000/` untuk profile dan projects
   - `http://127.0.0.1:8000/experience/` untuk experience
   - `http://127.0.0.1:8000/award/` untuk awards

### Menjalankan Test

```bash
python manage.py test
```

### Menjalankan dengan Konfigurasi Produksi (PostgreSQL)

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

Untuk menyiapkan static files pada deployment, jalankan:

```bash
python manage.py collectstatic --noinput
```

### Deployment

Aplikasi ini dideploy di domain PWS (Pacil Web Service) Fasilkom UI: <a href="https://adrian-nathanael-portfolio.pws.cs.ui.ac.id">Akses Disini</a>.

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

### Assignment 2

1. Saat membuka page portfolio, django memproses request melalui beberapa komponene seperti:
   - Project `urls.py`:  ini yang akan merender main application, dan juga admin page
   - Main `urls.py`:  ini lah komponen yang merender aplikasi utama kita yaitu home page, award page, dan experience page
   - View:  View berfungsi menangani logika dari request tersebut. View akan mengambil data yang diperlukan, biasanya melalui model. Setelah data diperoleh, view mengirimkan data tersebut ke template menggunakan context.
   - Model: Model berfungsi sebagai representasi data yang tersimpan di database. contohnya saat kita mengambil data dari semua award dengan 
      `award = award.objects.all()`
   - Template: Template menerima data dari view dan mengubahnya menjadi tampilan HTML. Data tersebut dapat ditampilkan menggunakan template syntax Django

2. Jika menggunakan pendekatan sebelumnya yang mana kita tulis langsung di template, jika di masa depan kita ingin menambahkan data baru maka kita harus membongkar ulang source code templatenya dan melakukan deploy applikasi yang baru, sedangkan dengan pendekatan baru ini ada beberapa keuntungan yang bisa kita rasakan diantaranya: 
   - Jika ingin menambahkan data baru kita tinggal menambahkan bisa melalui admin page ataupun scripting dan applikasi kita tidak berubah tetap aplikasi yang lama
   - Saat render di template, pendekatan ini memudahkan kita karena kita tinggal membuat salah template utamanya dan lakukan for loop untuk render datanya

3. `makemigrations` merupakan script untuk membuat file migrasi yang nantinya file ini berada di `migrations/` file ini merupakan generated django yang aslinya merupakan script untuk membuat table sql, namun alih-alih membuat file migrasi sql manual django memudahkan kita dengan membuatkan file yang bisa kita running dengan menggunakan script `migrate` untuk memasukan perubahan terhadap table kedalam database kita. misalnya saat kita membuat model baru `roles` dengan fieldsnya, saat kita jalankan `makemigrations` django membuatkan file migrasi terhadap model `roles` tersebut. di database, tabel `roles` tersebut belum ada sampai kita menjalankan script `migrate`.  

### AI Disclosure

## Assignment 1
* Saat menngerjakan project ini saya menggunakan AI web based untuk membantu saya dalam melakukan dokumentasi project saya. Saya memberikan AI tugas untuk membuat penjelasan tentang tech stack, project structure, dan cara untuk menjalankan project ini. Hasil dari AI ini saya review kembali dan pastikan bahwa langkah-langkah yang di tulis AI sudah sesuai. 

* Selain itu, saya juga menggunakan AI Copilot untuk membatu saya dalam menulis kode, tentunya karena AI ini memeberikan suggestion dari line dimana saya sedang bekerja, otomatis saya langsung mereview inline suggestion yang diberikan oleh AI copilot ini. 

## Assignment 2
* pada Assignment 2 saya menggunakan ai untuk melakukan migrasi dari section experience yang sebelumnya sudah perbah saya buat pada main page. Saya menggunakan AI untuk membuatkan script untuk seeding data berdasarkan data yang sudah pernah ada sebelumnya selain itu saya juga menggunakannya untuk memindahakan section itu ke template baru

* untuk workflow penggunaannya saya memintanya untuk melakukan pemindahan secara tdd sehingga setiap tugas yang saya berikan harus dia buatkan test dan juga setelah status tdd green baru diberikan kepada saya dan jika masih red harus diperbaiki terlebih dahulu. selain dengan ttd saya juga melakukan validasi lanjutan dengan runserver dan juga pengecekan terhadap kualitas kode yang dibuat oleh AI dan memperbaiki jika AI mengenerate kode yang sulit untuk dimaintain kedepannya

* Saya juga menggunakannya untuk melakukan perubahan terhadap design dan menurut hasil yang diberikan saya perlu melakukan prompt berulang kali karena hasil UI yang digenerate terkadang fail dan saat saya menggunakan AI untuk melakukan migrasi data hasilnya sudah baik sehingga berdasarkan penggunaan AI saya dalam assignment 2 ini saya mengambil sebuah kesimpulan bahwa AI sangat bisa digunakan untuk melakukan migrasi data dan belum cukup baik untuk digunakan dalam membuat UI tanpa validasi langsung dari saya. 

* Serta saya menggunakan AI untuk memperbaharui dokumentasi dari readme yang menjelaskan project structure dari project ini.

* model AI yang digunakan GPT-5.6-Luna (Xhigh)