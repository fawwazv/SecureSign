# Analisis Aplikasi iSign / DigiSign ITERA

Dokumen ini merangkum fitur, form, role, dan alur aplikasi berdasarkan video "Panduan Penggunaan iSign - Sistem Informasi Tanda Tangan Digital" (`digisign.itera.ac.id`).

**Catatan sumber:** analisis dilakukan dari tampilan layar video. Narasi audio tidak ikut terbaca. Bagian bertanda **(asumsi)** adalah inferensi saya karena tidak didemokan di video.

---

## 1. Gambaran Umum

iSign adalah sistem informasi tanda tangan elektronik untuk dokumen PDF di lingkungan kampus.

- **Login** melalui SSO kampus, ditambah captcha aritmatika (contoh: "Berapa hasil dari 4 x 2?").
- **Dua mode tanda tangan:**
  - **BSrE**: tanda tangan tersertifikasi, memakai passphrase sertifikat.
  - **Hanya QR**: dokumen diberi QR verifikasi tanpa sertifikat.
- **Aturan sejak 23 Januari 2026:** setelah pengajuan dibuat, pemohon langsung membubuhkan QR/stempel tanpa menunggu verifikasi dari penanda tangan.
- **Bulk:** pengajuan banyak file sekaligus. Semua file harus berukuran halaman yang sama.
- **Verifikasi dokumen** dapat dilakukan di dalam aplikasi, di `bsre.bssn.go.id/verify`, atau di `tte.komdigi.go.id/verifyPDF`.
- **FAQ** di dashboard memuat error umum: "This document probably uses a compression technique which is not supported by the free parser shipped with FPDI". Error ini muncul jika PDF pernah dikompresi aplikasi lain (Smallpdf, iLovePDF, dan sejenisnya). Solusi di rancangan baru: normalisasi PDF di sisi server sebelum diproses.

---

## 2. Struktur Menu

| Menu | Submenu | Keterangan |
|---|---|---|
| Dashboard | - | Kartu statistik dan FAQ |
| Master Data | Kategori, Stempel | Hanya tampil untuk akun admin |
| Pengajuan → Dokumen | Pengajuan, Bulk | Pembuatan dan daftar pengajuan |
| Pengajuan → BSrE | Status Pengguna, Verifikasi, Tutorial, Log Esign | Fitur terkait sertifikat dan verifikasi file |
| Verifikasi | - | Validasi pengajuan oleh penanda tangan |
| Verifikasi (Mahasiswa) | - | Tidak didemokan **(asumsi)** |
| Tembusan | - | Tidak didemokan **(asumsi)** |
| Penomoran | - | Tidak didemokan **(asumsi)** |
| Keluar | - | Logout |

---

## 3. Role

Satu pengguna dapat memiliki lebih dari satu role.

| Role | Hak akses utama | Sumber |
|---|---|---|
| **Pemohon** (dosen, pegawai, tendik) | Membuat pengajuan, TTD pribadi, bulk, menempatkan QR/stempel, mengunduh hasil | Video |
| **Penanda Tangan** (pejabat) | Menerima atau menolak pengajuan, menandatangani dengan passphrase BSrE | Video |
| **Pemaraf** | Memberi paraf pada dokumen. Tipenya berbeda dari tanda tangan dalam satu pengajuan | Video (pilihan Paraf/Tanda Tangan) |
| **Penerima Tembusan** | Melihat dokumen final yang ditembuskan kepadanya | Video |
| **Admin Unit** | Mengelola Kategori dan Stempel, melihat Log Esign | Video (Master Data) |
| **Petugas Penomoran** | Menerbitkan nomor dokumen atas permintaan pemohon | Video (kolom Permintaan Penomoran) |
| **Mahasiswa** | Mengajukan dan/atau diverifikasi | **Asumsi** (menu Verifikasi Mahasiswa) |
| **Super Admin** | Kelola user, role, konfigurasi, dan audit | **Asumsi** |
| **Publik** | Memverifikasi dokumen lewat QR tanpa login | Video dan asumsi |

---

## 4. Fitur

### 4.1 Autentikasi
- Login SSO (email dan password kampus) dengan captcha.
- Link "Lupa password? klik di sini" mengarah ke layanan SSO.
- Logout melalui menu Keluar.

### 4.2 Dashboard
- Empat kartu statistik:
  - **Total Tanda Tangan**
  - **Tanda Tangan Pribadi**
  - **Pengajuan Tanda Tangan**
  - **Permintaan Tanda Tangan** (permintaan yang masuk ke saya sebagai penanda tangan)
- Bagian FAQ berbentuk accordion:
  1. Apa itu aplikasi DigiSign ITERA? (aplikasi untuk membubuhkan QR code pada file PDF)
  2. Siapa yang dapat menggunakan aplikasi DigiSign ITERA? (seluruh civitas: mahasiswa, dosen, maupun tendik)
  3. Terkena error FPDF (masalah kompresi PDF)
  4. Bingung cara menggunakan aplikasi? (mengarah ke panduan PDF)

### 4.3 Daftar Pengajuan (Dokumen → Pengajuan)
- Banner informasi tentang perubahan alur sejak 23 Januari 2026.
- Tabel dokumen dengan pencarian, jumlah baris per halaman, dan paginasi.
- Kolom: No, Judul, Kategori, Tanggal, Status, Draft, Aksi.
- Status yang terlihat: **Disetujui** (hijau) dan **Menunggu** (biru).
- Tombol **Pribadi** dan **Pengajuan** di kanan atas tabel.
- Kolom Aksi berisi ikon per dokumen, misalnya edit QR, tanda tangan, dan unduh dokumen BSrE.

### 4.4 Pengajuan Penanda Tangan
- Upload PDF (drag and drop atau klik). Hanya PDF yang diterima.
- Pilihan **Tanda Tangan**: BSrE atau Hanya QR.
- Pilihan **Jenis dokumen**: Lainnya, Peraturan, Instruksi, Surat Edaran, Keputusan, Surat Tugas, Surat Dinas, Surat Undangan, Nota Dinas, Memo, Berita Acara, Surat Keterangan, Surat Pengantar, Laporan.
- Judul pengajuan.
- Penanda tangan/pemaraf lebih dari satu (multi-baris) dengan pilihan Paraf atau Tanda Tangan.
- Permintaan penomoran dokumen (opsional).
- Tembusan (opsional).
- Aturan yang ditampilkan di form:
  1. Jika memilih tanda tangan BSrE, pastikan para penanda tangan sudah memiliki akun BSrE.
  2. Setelah upload file, langsung bubuhkan QR pada menu yang telah disediakan.

### 4.5 Editor QR / Stempel (Pembubuhan QR)
- Preview dokumen per halaman ("Halaman 1", "Halaman 2", dan seterusnya).
- Tombol **Tambah QR (Bisa > 1)**: QR dapat ditambahkan lebih dari satu (fitur versi terbaru).
- Tombol **Tambah Stempel**: memilih stempel berdasarkan unit kerja (contoh: Stempel FTI 2025, Stempel FTIK 2025, Stempel FS 2025, Stempel Perpustakaan 2025).
- Penghitung "Total QR" dan status "Stempel: Belum Ada".
- QR dan stempel dapat digeser dan diubah ukurannya di atas halaman PDF.
- Instruksi di atas kanvas menyarankan penggunaan perangkat desktop.
- Checkbox konfirmasi: "Saya yakin posisi QR Code sudah sesuai dan siap untuk diproses", lalu tombol **Simpan**.

### 4.6 Tanda Tangan Pribadi
- Pengguna menandatangani dokumennya sendiri tanpa penanda tangan lain.
- Alur: upload, isi jenis dan judul, tempatkan QR, lalu menandatangani dengan passphrase.
- Setelah berhasil muncul pesan "Dokumen berhasil ditandatangani".

### 4.7 Pengajuan Bulk
- Halaman daftar Pengajuan Bulk (dengan tombol Pribadi dan Pengajuan).
- Form pengajuan bulk memuat upload banyak file dan setelan penanda tangan yang berlaku untuk semua file.
- Aturan tambahan: semua file harus memiliki ukuran panjang dan lebar halaman yang sama, agar posisi QR seragam.

### 4.8 Verifikasi (sisi Penanda Tangan)
- Tiga tab: **Belum Divalidasi**, **Diterima**, **Ditolak**.
- Kolom: No, Nama Pemohon, Judul, Status, Tanggal, Aksi.
- Halaman **Detail Pengajuan**: judul, kategori, pemohon, status, dan waktu pengajuan.
- Bagian **Dokumen (Final)** menampilkan preview PDF (zoom, unduh, cetak).
- Panel **Penanda Tangan** menampilkan nama, jabatan, tipe (Tanda Tangan/Paraf), dan status. Panel **Tembusan** menampilkan penerima tembusan.
- Form Validasi Dokumen: lihat bagian 5.

### 4.9 BSrE
- **Status Pengguna:** cek status akun/sertifikat BSrE (contoh tampilan: "Status Sertifikat Anda ISSUE").
- **Verifikasi:** upload file yang sudah ditandatangani untuk dicek keabsahannya. Hasil valid: "Dokumen valid, Sertifikat yang digunakan terpercaya".
- **Tutorial:** halaman berisi video tutorial pembuatan akun BSrE (embed YouTube, disertai link cadangan jika video tidak tampil).
- **Log Esign:** riwayat proses tanda tangan elektronik.

### 4.10 Master Data (Admin)
- **Kategori:** daftar jenis dokumen.
- **Stempel:** stempel per unit kerja dan tahun.

### 4.11 Penomoran dan Tembusan (asumsi)
- **Penomoran:** petugas menerbitkan nomor dokumen sesuai pola unit dan kategori, contoh nomor pada video: `B/7154/IT9.E2/HM.00.01/2025`.
- **Tembusan:** daftar dokumen yang ditembuskan kepada saya.

### 4.12 Verifikasi Publik
- QR pada dokumen mengarah ke halaman verifikasi tanpa login.
- Halaman menampilkan metadata dokumen, status, dan penanda tangan.
- Pengguna dapat mengunggah PDF untuk membandingkan keasliannya **(asumsi)**.
- Verifikasi tambahan tersedia di layanan resmi BSSN dan Komdigi (PDFSign). Hasil di Komdigi menampilkan "Dokumen ini memiliki tanda tangan digital".

### 4.13 Fitur Pendukung yang Disarankan
- Notifikasi (in-app dan email) untuk pengajuan baru, hasil validasi, dan dokumen selesai.
- Alasan penolakan saat penanda tangan menolak.
- Pembatalan pengajuan oleh pemohon sebelum disetujui.
- Audit log seluruh aksi penting.

---

## 5. Form

### 5.1 Login SSO
| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| Email | teks | Ya | Email SSO kampus |
| Password | password | Ya | |
| Hasil captcha | angka | Ya | Pertanyaan aritmatika acak |

### 5.2 Pengajuan Penanda Tangan
| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| File dokumen | upload | Ya | Hanya PDF |
| Tanda Tangan | pilihan | Ya | BSrE / Hanya QR |
| Jenis | pilihan | Ya | Daftar jenis dokumen (bagian 4.4) |
| Judul | teks panjang | Ya | |
| Penanda Tangan/Paraf: Nama Pegawai | autocomplete | Ya | Ketik minimal 3 karakter |
| Penanda Tangan/Paraf: Jabatan | teks | Ya | Terisi otomatis dari pegawai, dapat disesuaikan |
| Penanda Tangan/Paraf: Tipe | radio | Ya | Paraf / Tanda Tangan |
| Tombol Tambah | aksi | - | Menambah penanda tangan ke daftar (dapat dihapus) |
| Permintaan Penomoran Dokumen | autocomplete | Tidak | Pilih petugas penomoran |
| Tembusan (tab Pegawai) | autocomplete multi | Tidak | Tombol Tambah, tombol hapus per baris |
| Tombol Simpan | aksi | - | Membuat pengajuan lalu membuka Editor QR |

Aturan validasi:
- Jika memilih BSrE, seluruh penanda tangan wajib punya akun BSrE aktif.
- Minimal satu penanda tangan.
- Pesan sukses: "Pengajuan berhasil dibuat".

### 5.3 Pengajuan Tanda Tangan Pribadi
| Field | Tipe | Wajib |
|---|---|---|
| File dokumen (PDF) | upload | Ya |
| Jenis | pilihan | Ya |
| Judul pengajuan | teks panjang | Ya |

Info di form: "Silahkan isi dengan lengkap, semua wajib diisi."

### 5.4 Pengajuan Bulk
| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| File dokumen | upload banyak | Ya | PDF, ukuran halaman harus sama |
| Tanda Tangan | pilihan | Ya | BSrE / Hanya QR |
| Jenis | pilihan | Ya | |
| Penanda tangan/paraf | seperti 5.2 | Ya | Berlaku untuk semua file |
| Permintaan penomoran | autocomplete | Tidak | |
| Tembusan | autocomplete multi | Tidak | |

### 5.5 Editor QR
| Elemen | Keterangan |
|---|---|
| Kanvas PDF | Dokumen per halaman, QR/stempel dapat digeser dan diubah ukurannya |
| Tambah QR (Bisa > 1) | Menambah QR baru |
| Tambah Stempel | Memilih unit kerja lalu stempel |
| Checkbox konfirmasi | Wajib dicentang sebelum Simpan |
| Simpan | Mengirim pengajuan ke penanda tangan |

### 5.6 Validasi Dokumen (Penanda Tangan)
| Field | Tipe | Wajib | Keterangan |
|---|---|---|---|
| Validasi | pilihan | Ya | TERIMA / TOLAK |
| Passphrase | password | Ya bila TERIMA dengan BSrE | Tidak boleh disimpan atau dicatat di log |
| Saya tidak memakai BSrE | checkbox | Tidak | Menyelesaikan sebagai mode QR |
| Alasan penolakan | teks panjang | Ya bila TOLAK | **Usulan**, belum terlihat di video |
| Simpan | aksi | - | |

Info di form: "Pemohon meminta untuk menandatangani dengan BSrE".

### 5.7 Tanda Tangan Pribadi (Sign)
| Field | Tipe | Wajib |
|---|---|---|
| Preview dokumen | tampilan | - |
| Passphrase | password | Ya |
| Sign | aksi | - |



### 5.9 Master Kategori (asumsi)
| Field | Tipe | Wajib |
|---|---|---|
| Nama kategori | teks | Ya |
| Kode | teks | Ya |
| Status aktif | toggle | Ya |

### 5.10 Master Stempel (asumsi)
| Field | Tipe | Wajib |
|---|---|---|
| Nama stempel | teks | Ya |
| Unit kerja | pilihan | Ya |
| Tahun | angka | Ya |
| Gambar stempel | upload | Ya |
| Status aktif | toggle | Ya |

---

## 6. Alur Aplikasi

### 6.1 Login
1. Pengguna membuka `digisign.itera.ac.id`, lalu diarahkan ke halaman SSO.
2. Mengisi email, password, dan captcha.
3. Setelah berhasil, masuk ke Dashboard.

### 6.2 Pengajuan dengan Penanda Tangan (alur baru sejak 23 Januari 2026)
1. Pemohon membuka **Dokumen → Pengajuan**, lalu klik **Pengajuan**.
2. Mengunggah PDF, memilih BSrE atau Hanya QR, jenis, dan mengisi judul.
3. Menambahkan penanda tangan/pemaraf, penomoran (opsional), dan tembusan (opsional).
4. Klik **Simpan**. Sistem membuat pengajuan dan menampilkan "Pengajuan berhasil dibuat".
5. Pemohon otomatis masuk ke **Editor QR**, menempatkan QR dan stempel, mencentang konfirmasi, lalu **Simpan**.
6. Pengajuan berstatus **Menunggu** dan penanda tangan mendapat notifikasi.
7. Penanda tangan membuka **Verifikasi → Belum Divalidasi**, lalu membuka Detail Pengajuan dan memeriksa preview dokumen.
8. Penanda tangan memilih:
   - **TOLAK**: pengajuan pindah ke tab Ditolak dan pemohon diberi tahu.
   - **TERIMA dengan BSrE**: mengisi passphrase, lalu sistem menandatangani dokumen.
   - **TERIMA tanpa BSrE**: mencentang "Saya tidak memakai BSrE", lalu dokumen diselesaikan sebagai mode QR.
9. Bila masih ada penanda tangan/pemaraf berikutnya, ulangi langkah 7 dan 8.
10. Setelah semua selesai, status menjadi **Disetujui**. Dokumen final muncul di tab Diterima dan dapat diunduh oleh pemohon. Penerima tembusan dapat melihatnya.

### 6.3 Tanda Tangan Pribadi
1. Klik tombol **Pribadi** di halaman Pengajuan.
2. Upload PDF, pilih jenis, isi judul, lalu **Simpan**.
3. Tempatkan QR di Editor QR dan simpan.
4. Buka halaman Sign, isi passphrase, klik **Sign**.
5. Muncul "Dokumen berhasil ditandatangani". Dokumen berstatus Disetujui dan dapat diunduh dari kolom Aksi.

### 6.4 Pengajuan Bulk
1. Buka **Dokumen → Bulk**, lalu klik **Pengajuan**.
2. Upload banyak PDF. Sistem memeriksa ukuran halaman seragam.
3. Isi penanda tangan, jenis, penomoran, dan tembusan yang berlaku untuk semua file.
4. Tempatkan QR sekali. Posisi yang sama diterapkan ke semua file.
5. Sistem memproses per file dan menampilkan hasilnya di daftar Bulk.

### 6.5 Cek Status BSrE dan Tutorial
1. Buka **BSrE → Status Pengguna** untuk melihat status sertifikat (contoh: ISSUE).
2. Bila belum punya akun, buka **BSrE → Tutorial** dan ikuti video pembuatan akun.

### 6.6 Verifikasi Dokumen
- **Di aplikasi:** BSrE → Verifikasi, upload file TTD, isi password bila ada, klik **Verifikasi**. Hasil: "Dokumen valid, Sertifikat yang digunakan terpercaya".
- **Di layanan resmi:** unggah PDF di `bsre.bssn.go.id/verify` atau `tte.komdigi.go.id/verifyPDF`. Hasil menampilkan informasi dokumen dan keterangan "Dokumen ini memiliki tanda tangan digital".
- **Publik lewat QR:** scan QR pada dokumen, halaman verifikasi menampilkan data dokumen dan penanda tangan.

### 6.7 Status Dokumen
```
DRAFT → MENUNGGU → DISETUJUI
                 ↘ DITOLAK
DRAFT / MENUNGGU → DIBATALKAN (oleh pemohon, usulan)
```

---

## 7. Catatan Implementasi (Vue + FastAPI)

- **Vue:** tampilan PDF memakai `pdf.js`. Editor QR berupa kanvas yang dapat digeser, dengan koordinat disimpan per halaman.
- **FastAPI (kriptografi):**
  - Normalisasi PDF (pikepdf/qpdf) untuk mencegah error kompresi seperti pada FAQ.
  - Hash SHA-256 untuk file asli dan file final.
  - QR berisi URL verifikasi dengan token acak (`secrets.token_urlsafe`).
  - Overlay QR/stempel dengan PyMuPDF. Perhatikan konversi koordinat layar (asal kiri-atas) ke PDF (asal kiri-bawah).
  - Tanda tangan BSrE lewat klien API BSrE. Kontrak endpoint harus mengikuti dokumentasi resmi.
  - Verifikasi tanda tangan PDF dengan pyHanko.
- **Keamanan:**
  - Passphrase tidak boleh disimpan, dicatat, atau masuk ke log.
  - File disimpan privat dan diakses lewat URL berumur pendek.
  - Halaman verifikasi publik dibatasi rate limit dan hanya menampilkan data minimum.
  - Otorisasi dicek di server pada setiap aksi.
  - Dokumen yang sudah disetujui tidak dapat diubah.
  - Audit log bersifat append-only.

---

## 8. Hal yang Perlu Dikonfirmasi

1. Detail fitur **Penomoran**, **Tembusan**, dan **Verifikasi (Mahasiswa)** karena tidak didemokan.
2. Apakah penanda tangan berjenjang harus berurutan atau boleh paralel.
3. Spesifikasi API BSrE (endpoint, parameter, tampilan tanda tangan visible atau invisible).
4. Peran mahasiswa: boleh mengajukan sendiri atau hanya diverifikasi.
