# Catatan Revisi — PinjamLab v5.0

**Tampilan:** penyempurnaan tema Lab Journal Edition dengan latar kertas-krem, editorial hijau tua, aksen lime, instrumen orbit/radar, mikroanimasi ikon, kedalaman panel dan transisi hover yang lebih konsisten. Animasi bekerja otomatis menggunakan transform/opacity, tanpa tombol kontrol animasi atau label status gerakan. Tetap mematuhi preferensi `prefers-reduced-motion` perangkat.

**Dashboard fungsional:** panel tiga tindakan yang membuka halaman dengan filter terkait; nilai ketersediaan/aktivitas/perawatan dari SQLite; tautan untuk muat ulang dan tombol penyalin ringkasan (dengan tanggapan keberhasilan/gagal dan izin clipboard). Angka tidak diperbarui realtime di luar pemuatan ulang halaman.

**Perubahan teknis:** struktur route CRUD, validasi server, CSRF, SQLite, data persisten, port, login-free localhost dan Docker tetap dipertahankan; `/health` menampilkan versi `5.0`. Aset CSS/JS lokal tanpa ketergantungan CDN. Semua kontrol yang tampil punya tindakan yang nyata. Panel radar dan elemen cahaya adalah ilustrasi, bukan data telemetri sensor.

**Yang diuji pada pembuatan paket:** 8/8 uji aturan bisnis; 9/9 template dirender untuk pemeriksaan visual (dengan data contoh); 45/45 kombinasi halaman+lebar layar di Chromium tanpa overflow horizontal dan tanpa exception JS; Ctrl+K/Esc, pencarian menu, sorting tabel, validasi batas tanggal, salin ringkasan dengan clipboard mock; sintaks JavaScript dan parse stylesheet. File ZIP akan dilengkapi checksum SHA-256.

**Yang tidak bisa dipastikan dari pengujian ini:** 48 uji penuh di Flask/Gunicorn serta Docker Desktop, restore/persistensi sesungguhnya di PC, dan nilai dosen. Jalankan `UJI_WEBSITE.cmd` di Windows saat Docker Desktop aktif. Rubrik resmi dosen tidak disertakan; `CHECKLIST_PENILAIAN.md` adalah daftar periksa berdasarkan laporan, bukan jaminan nilai.

**Dokumentasi akademik:** laporan PDF/Word dari versi lama harus diperbarui dengan gambar halaman baru dan bukti pengujian aktual versi final. Jangan menyatakan pengujian Docker lulus tanpa log pelaksanaan nyata.


## Audit lanjutan — 26 Oktober 2026

- Menambah pemeriksaan ulang transaksi peminjaman **di dalam transaksi tulis**, sehingga data yang dihapus atau berubah saat dua request bersamaan tidak keliru diaudit sebagai pembaruan berhasil.
- Pengembalian bersamaan kini membedakan respons berhasil pertama dan respons kedua yang mendapati transaksi sudah selesai. Perubahan inventaris tetap atomik.
- Menambahkan `Vary: Cookie` pada respons yang memakai sesi/CSRF; mempertahankan `Cache-Control: no-store` dan perlindungan CSRF yang sudah ada.
- Mengganti perilaku scroll reduced-motion menjadi nilai standar `auto`.
- Menambahkan tujuh uji integritas SQLite yang berjalan pada database sementara (tidak mengubah database operasional) dan memasukkannya ke skrip pengujian Docker.
- Hasil audit lokal: 8/8 aturan, 7/7 integritas SQLite, 9/9 template Jinja, 45/45 kombinasi browser tanpa overflow/exception, 7/7 interaksi browser, JavaScript dan Python berhasil diperiksa sintaksnya. **Pengujian Flask, Gunicorn, Compose, dan persistence nyata memerlukan Docker di komputer penguji; belum dinyatakan lulus dari audit lokal ini.**
- Laporan Word sumber tetap tidak ditimpa: tautan repo/video, bukti Docker dan bagian versi 2.1 perlu diselaraskan setelah uji mesin sebenarnya.

## Pembaruan video kedua: satu fitur sederhana

- Menambahkan **Salin kode** pada setiap baris Data Alat (sebelumnya kode hanya berupa teks).
- Perubahan hanya pada `templates/equipment_list.html`, `static/app.js`, dan `static/style.css`; bagian README ini mendokumentasikan pembaruan.
- Tidak ada perubahan backend, skema SQLite, Docker Compose, atau fitur CRUD lama.
- Verifikasi: buka Data Alat pada `http://127.0.0.1:8080`, klik Salin kode, lalu `Ctrl + V` pada pencarian untuk mencocokkan kode; dokumentasikan build/restart Docker dalam video kedua.
