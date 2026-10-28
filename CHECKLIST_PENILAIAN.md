# Checklist Kesiapan Penilaian PinjamLab v5.0

> Ini **bukan rubrik resmi dosen**. Daftar berikut disusun dari kebutuhan yang dijelaskan dalam laporan Tugas Kelompok 1 MID Pengenalan DevOps. Penilaian 100 tidak dapat dijamin tanpa rubrik dan evaluasi penguji.

- [x] Identitas kelompok, topik dan manfaat aplikasi dijelaskan pada `PROJECT_INFO.md`.
- [x] CRUD inventaris dan CRUD peminjaman terdapat di `app.py`.
- [x] SQLite mempunyai relasi, constraint, serta audit pada `schema.sql`.
- [x] Satu peminjaman aktif per unit dan batas maksimal 7 hari ditegakkan dalam database/validasi.
- [x] Dockerfile, Compose, healthcheck, port localhost, non-root dan named volume tersedia di source.
- [x] Script pembuka Windows, penyiapan `.env`, seed contoh, backup dan uji tersedia.
- [x] Dashboard, pencarian, filter, bukti transaksi, CSV dan log audit tersedia.
- [x] Antarmuka responsif, animasi dekoratif otomatis, dukungan pengurangan gerak.
- [x] Pemeriksaan browser 9 halaman × 5 ukuran, tanpa exception JS/overflow dalam pratinjau.
- [x] Uji aturan bisnis 8/8 dijalankan berhasil pada lingkungan pemeriksaan ini.
- [x] Lulus **7/7 tes integritas SQLite terisolasi** di lingkungan audit 26 Oktober 2026.
- [x] 9 halaman pratinjau × 5 lebar di Chromium: tidak ada overflow halaman dan tidak ada error JS.
- [ ] Jalankan **48 uji aplikasi/HTTP + 7 uji SQLite** pada lingkungan Docker sebenarnya dengan `UJI_WEBSITE.cmd`.
- [ ] Dokumentasikan hasil build image, startup container, healthcheck dan uji persistensi volume.
- [ ] Perbarui screenshot/versi dalam laporan Word/PDF agar sesuai dengan website v5.0.
- [ ] Verifikasi tautan repository GitHub, video demonstrasi dan persyaratan pengumpulan dengan dosen.
- [ ] Cocokkan dengan **rubrik resmi** bila sudah diterima.
