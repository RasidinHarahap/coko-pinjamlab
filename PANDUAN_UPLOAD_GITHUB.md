# Panduan update PinjamLab v5.0 ke GitHub

**Repository yang dituju:** https://github.com/RasidinHarahap/coko-pinjamlab  
**Branch:** `main`  
**Catatan:** Push source ke GitHub **bukan** hosting Flask di GitHub Pages.

## Cara termudah (Windows)

1. **Extract All** berkas ZIP yang diunduh, misalnya `pinjamlab_github_readme_premium_v5.zip`, ke sebuah folder baru. Jangan menjalankan skrip dari dalam ZIP.
2. Pasang **Git for Windows** dari https://git-scm.com/downloads/win jika belum ada. Setelah instalasi, tutup dan buka ulang jendela Explorer/terminal agar perintah `git` terbaca.
3. Opsional dan direkomendasikan: pasang **GitHub CLI** dari https://cli.github.com/ agar login GitHub melalui browser mudah. Tanpa `gh`, Git Credential Manager pada Git for Windows dapat meminta login ketika push.
4. Klik dua kali **`UPLOAD_KE_GITHUB.cmd`**.
5. Jika diminta, selesaikan login browser GitHub sebagai akun dengan izin **Write** ke `RasidinHarahap/coko-pinjamlab`.
6. Periksa ringkasan berkas yang akan diunggah. Ketik tepat **YA** untuk mengizinkan commit dan push ke `main`.
7. Tunggu pesan **Upload berhasil**, lalu buka https://github.com/RasidinHarahap/coko-pinjamlab dan tab **Actions**. Workflow dapat memerlukan izin Actions di repository.

### Bila Git for Windows belum terpasang
Buka PowerShell sebagai pengguna biasa lalu instal dari website resmi di atas. Anda juga bisa menggunakan `winget install --id Git.Git -e` jika Winget tersedia. **Restart terminal** sebelum mencoba lagi.

### Bila belum pernah mengatur identitas Git
Skrip meminta nama dan email commit secara interaktif. Isi email yang Anda pakai pada pengaturan GitHub atau email noreply milik akun Anda. Jangan masukkan password atau personal access token ke source ataupun `.env.example`.

## Yang dilakukan skrip

- Clone **branch `main` terbaru** dari repository target ke direktori sementara.
- Salin **hanya file yang ada di `MANIFEST_GITHUB.txt`**, bukan seluruh folder pengguna.
- Menampilkan daftar perubahan, lalu meminta konfirmasi `YA`.
- Commit perubahan dan push **tanpa `--force`**, sehingga update baru di GitHub yang bertabrakan tidak ditimpa paksa.
- Tidak menghapus file lama yang tidak tercantum dalam paket.
- Tidak menyalin `.env`, database `.sqlite3`, file log, dan folder `.local`.

Jika GitHub menolak push, periksa status akun, izin repository, aturan branch protection, dan koneksi internet. Jika ada commit baru saat skrip berjalan, jalankan ulang supaya clone mengambil versi terbaru. Jangan menggunakan force push.

## README dengan screenshot autentik

README versi ini menampilkan screenshot dashboard, daftar inventaris, dan formulir peminjaman dari dokumentasi laporan versi 5.0. Ketiga gambar disimpan di `docs/screenshots/` dan **sudah didaftarkan dalam `MANIFEST_GITHUB.txt`** agar ikut terunggah otomatis bersama README. Jangan menghapus folder tersebut sebelum upload.

## Setelah source terunggah: pengujian otomatis

File `.github/workflows/verify.yml` menyediakan **continuous integration (CI)** setiap push ke `main` atau pull request. GitHub Actions akan membangun image, menjalankan container, healthcheck, 7 uji integritas SQLite, 8 uji aturan bisnis, 27 uji integrasi Flask, 13 uji HTTP dan pemeriksaan persistensi volume.

Workflow ini **tidak** mempublikasikan website ke GitHub Pages, membuat rilis produksi, atau memindahkan database dari laptop. Status hijau hanya berlaku jika workflow GitHub Actions benar-benar menyelesaikan pengujian.

## Menjalankan website pada laptop

1. Buka Docker Desktop sampai status engine menyala (Linux containers).
2. Jalankan `MULAI_DI_SINI.cmd`, lalu buka http://127.0.0.1:8080.
3. Jalankan `UJI_WEBSITE.cmd` untuk melihat pemeriksaan Docker lokal. Uji ini membuat ulang container namun mempertahankan named volume.
4. **Jangan jalankan `docker compose down -v` jika data penting ingin dipertahankan.**

## Jika ingin memperbarui lagi

Edit source di folder paket, lalu jalankan `UPLOAD_KE_GITHUB.cmd` kembali. Setiap file baru yang ingin ikut terkirim perlu dicantumkan pada `MANIFEST_GITHUB.txt` terlebih dahulu. Jika perlu menghapus berkas lama di GitHub, lakukan review dan hapus lewat commit yang terpisah.

## Batasan

Pemeriksaan sintaks dan sejumlah pengujian Python dapat dilakukan sebelum upload; keberhasilan operasi Windows/GitHub dan Docker hanya bisa dipastikan saat dijalankan pada perangkat dengan koneksi dan akses yang sesuai. Website masih dirancang untuk **localhost tanpa autentikasi** dan tidak boleh diekspos langsung ke internet.
