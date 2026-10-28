# Hasil Audit PinjamLab — 26 Oktober 2026

## Dasar pemeriksaan

Source: `pinjamlab(8).zip` (versi aplikasi 5.0). Acuan: laporan `Tugas01_231110869(1).docx`, khususnya kriteria *penggunaan container* (40), *originalitas* (30), *CRUD* (10), *database* (10), serta *kelengkapan/kerapian laporan* (10). Laporan menyebut video/repository versi lama 2.1 meskipun pembahasan source versi 5.0. Nilai akhir merupakan kewenangan dosen.

## Apa yang sudah dikonfirmasi

1. Struktur source: Flask/Jinja, Gunicorn, SQLite, Dockerfile, Compose, skrip pembuka Windows, formulir alat/peminjaman/pengembalian, halaman bukti, ekspor CSV, jejak audit. Tidak ada server database terpisah karena SQLite tertanam.
2. Aturan domain: satu kode per unit, kondisi layak pinjam, maksimal tujuh hari, larangan tanggal pinjam masa depan, satu transaksi aktif per unit, kondisi pengembalian memperbarui inventaris secara atomik.
3. Pengujian benar-benar dijalankan dalam audit ini: **8/8 tes aturan bisnis**, **7/7 regresi SQLite pada database terisolasi**, **9/9 template Jinja dirender**, **45/45 tampilan Chromium pada 320, 390, 768, 1280, 1440 px tanpa overflow horizontal halaman ataupun exception JS**. Selain itu 7/7 interaksi pada pratinjau Chromium berhasil (Ctrl+K, pencarian dialog, Escape, salin ringkasan, batas 7 hari pada form, catatan kondisi rusak, dan pengurutan tabel). Pemeriksaan sintaks Python dan JS berhasil.
4. Bukti print diperiksa dalam pratinjau CSS; hasil cetak A4 melalui printer/browser sesungguhnya belum diverifikasi pada perangkat pengguna.

## Perbaikan yang diterapkan

- `app.py`: pemeriksaan ulang transaksi di dalam lock transaksi SQLite sebelum UPDATE; menghindari audit palsu akibat data terhapus/berubah di sela proses edit.
- `app.py`: pengembalian kedua yang bersamaan mengembalikan informasi bahwa transaksi telah selesai, bukan mengklaim perubahan baru.
- `app.py`: `Vary: Cookie` untuk respons dengan sesi dan CSRF.
- `static/app.js`: scroll pada mode *reduce motion* menggunakan `auto`.
- `scripts/test_sqlite_integrity.py`: tujuh regresi baru, terisolasi, termasuk unique code, active loan, foreign key, batas tanggal, rollback, pencatatan kembali, backup, dan inisialisasi ulang; diintegrasikan dalam `scripts/uji.ps1`.

## Yang masih perlu bukti sebelum pengumpulan

- Jalankan `MULAI_DI_SINI.cmd` dan `UJI_WEBSITE.cmd` pada Windows dengan Docker Desktop aktif. Catat output healthcheck, 48 pengujian aplikasi/HTTP + 7 SQLite dan persistensi yang benar-benar lulus.
- Perbarui repository dan video demonstrasi agar menampilkan source ini, bukan hanya dokumentasi versi 2.1.
- Perbarui bagian klaim tes dan tangkapan layar dalam laporan Word bila kondisi pelaksanaan berbeda; jangan mencantumkan klaim pengujian yang belum dilakukan.
- Periksa perintah Compose dan ekspor/cetak PDF pada komputer sasaran. Jangan menjalankan `docker compose down -v` ketika data harus disimpan.

## Catatan batasan

Aplikasi masih untuk petugas pada localhost tanpa login/peran. Jangan diekspos ke internet. ZIP tidak berisi database, password, `.env`, screenshot buatan, atau rekaman video. Revisi source tidak menghapus data yang sudah ada pada named volume Docker. Pemeriksaan ini bukan jaminan nilai 100 atau lulus seluruh kondisi runtime pengguna.
