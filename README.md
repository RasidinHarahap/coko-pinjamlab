# PinjamLab - Tim Coko

Website Peminjaman Alat Laboratorium untuk Tugas Kelompok 1 MID Pengenalan DevOps.

Nama tim: **Coko**. Anggota: Rasidin Harahap (231110869), Ade Kurnia Setialu (231110333), dan Arsenius P. Sinaga (231111699).

Source dibuat khusus dengan bantuan ChatGPT/OpenAI Codex. Identitas, topik, penjelasan fitur, serta sumber kode dijabarkan pada [PROJECT_INFO.md](PROJECT_INFO.md).

Website peminjaman alat laboratorium dengan tampilan hijau modern, tiga menu utama, CRUD alat dan transaksi, serta database SQLite yang tersimpan di volume Docker. Aset tampilan tersedia lokal; tidak perlu Node.js, XAMPP, atau Python di laptop untuk cara Docker.

## Mulai di Windows

1. Klik kanan ZIP → **Extract All / Ekstrak Semua**. Buka folder hasil ekstrak. Jangan menjalankan CMD dari dalam ZIP.
2. Buka **Docker Desktop** dan tunggu **Engine running**. Gunakan Linux containers.
3. Klik dua kali **MULAI_DI_SINI.cmd**. Tunggu sampai tertulis **Website siap**. Browser terbuka otomatis; alamat bawaan **http://127.0.0.1:8080**.

Pertama kali perlu internet untuk mengunduh image Python dan paket Flask/Gunicorn. Proses berikutnya memakai cache Docker. File `.env` dibuat otomatis dengan kunci acak.

Jika browser tertutup, buka alamat yang sama. Setelah restart laptop, ulangi langkah 2–3. Jendela CMD boleh ditutup sesudah berhasil; container tetap berjalan selama Docker aktif. Pesan kesalahan tidak langsung hilang karena pembuka memakai CMD yang tetap terbuka. Log ada di `.local/LOG_MULAI.txt`.

Jika Docker belum terpasang: gunakan petunjuk resmi https://docs.docker.com/desktop/setup/install/windows-install/ . Jika port 8080 dipakai aplikasi lain, ubah `APP_PORT=8080` menjadi `APP_PORT=8081` di `.env`, lalu klik pembuka lagi.

## Pemakaian paling singkat

**Data alat → Tambah alat → Simpan → Ubah.** Lalu **Peminjaman → Catat peminjaman → Simpan → Ubah → Kembalikan**. Untuk menunjukkan hapus, hapus transaksi contoh dahulu, kemudian alatnya. Tombol Bukti menyediakan cetak/simpan PDF; Ekspor CSV dan Jejak aktivitas juga tersedia.

Saat database kosong, pembuka menambahkan 5 alat dan 3 transaksi contoh dengan peminjam/NIM berlabel DEMO. Data contoh tidak menggantikan data yang sudah ada. Buat data demonstrasi sendiri bila diperlukan. Kondisi rusak/perawatan tidak bisa dipinjam, satu alat hanya punya satu peminjaman aktif, dan peminjaman maksimal 7 hari. Status terlambat mengikuti tanggal WIB.

## Uji di Docker

Klik **UJI_WEBSITE.cmd** untuk membangun aplikasi, menjalankan 8 uji aturan + 27 uji SQLite/aplikasi + 13 uji HTTP, lalu membuat ulang container untuk membuktikan persistensi database. Tulisan LULUS hanya tampil jika semuanya berhasil. Website berhenti sebentar ketika container dibuat ulang, kemudian berjalan lagi. Log ada di `.local/LOG_UJI.txt`.

## Struktur dan teknologi

`app.py`: rute CRUD / `database.py`: koneksi dan transaksi / `rules.py`: validasi / `schema.sql`: tabel equipment, loans, audit_log / `templates/` dan `static/`: tampilan / `scripts/`: pembuka dan pengujian / `Dockerfile` dan `compose.yaml`: container.

Python 3.12, Flask 3.1.2, Gunicorn 23.0.0, SQLite, Jinja, HTML/CSS. Container memakai user non-root, healthcheck, dua worker, bind localhost, dan volume `appdata`. Proyek Compose tetap bernama `pinjamlab`; jika paket sebelumnya memakai nama itu di Docker yang sama, volume datanya digunakan kembali. Jangan menjalankan `docker compose down -v` karena menghapus volume database.

Terminal manual, dari folder yang memuat `compose.yaml`:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\jalankan.ps1
```

Pencadangan database, setelah website berjalan:

```powershell
$namaBackup = "pinjamlab-backup-$(Get-Date -Format yyyyMMdd-HHmmss).sqlite3"
docker compose exec -T web python scripts/backup_db.py "/app/data/$namaBackup"
docker compose cp "web:/app/data/$namaBackup" "./$namaBackup"
```

Simpan hanya source dalam repository; `.env`, database, dan log telah dikecualikan oleh `.gitignore`.

## Kredit dan referensi

Rasidin Harahap (231110869), Ade Kurnia Setialu (231110333), Arsenius P. Sinaga (231111699). Source dan desain disusun dengan bantuan OpenAI Codex; anggota perlu memahami aplikasi dan mencatat kontribusi yang benar pada laporan.

Rujukan teknis: https://flask.palletsprojects.com/ · https://docs.docker.com/compose/ · https://docs.python.org/3/library/sqlite3.html · https://docs.gunicorn.org/ .

ZIP ini berisi website dan file untuk menjalankan/menguji. Kelengkapan pengumpulan berupa laporan PDF, repository, dan rekaman proses tetap dibuat terpisah sesuai lembar tugas.
