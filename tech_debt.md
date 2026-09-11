# Tech Debt

> **Pembaruan 2026-09-11 — Section 1 (pisahkan data dari tampilan).**
> Ditutup: **#1** (sudah dibuka di browser sungguhan, CDN asli termuat, nol galat halaman) ·
> **#4** (template CSV usang diganti jembatan `data_csv.py` yang mengikuti skema nyata) ·
> **#10** (skema didokumentasikan di `SKEMA.md`).
> Dibuka baru: **#12** — grafik Tab 1 kosong saat halaman pertama dibuka.
> Sisanya masih terbuka dan dikerjakan di Section 2.

## Riwayat awal — sesi "Analisis Hama, Penyakit & Product Share"

Catatan hutang teknis dan hal yang belum tuntas dari sesi implementasi branch
`tingkat-serangan`. Ditulis supaya sesi/branch berikutnya tidak perlu
menebak-nebak apa yang sudah sengaja ditunda vs yang benar-benar terlewat.

## 1. Verifikasi visual production build belum pernah dilakukan

> ✅ DITUTUP 11 Sep — `index.html` yang asli dirender di browser sungguhan (Chromium, CDN asli termuat, nol galat halaman). Semua angka kartu statistik identik dengan versi sebelum pemisahan data. **Justru pemeriksaan inilah yang menemukan butir #12.**

Environment sandbox sesi ini **tidak punya akses keluar** ke
`cdn.tailwindcss.com`, `cdn.jsdelivr.net`, `unpkg.com`, maupun
`fonts.googleapis.com` (semua kena block 403 oleh proxy jaringan). Akibatnya:

- `index.html` yang sebenarnya (yang memakai CDN asli) **belum pernah
  di-screenshot / dibuka di browser sungguhan** selama sesi ini.
- Semua validasi dilakukan lewat simulasi logic di Node.js (stub DOM manual)
  yang menjalankan seluruh kombinasi 13 hama/penyakit × 8 territory × sub-territory
  dan memastikan tidak ada exception — ini memvalidasi **kebenaran data & logic**,
  bukan tampilan visual asli.
- Artifact preview yang dikirim ke Anda adalah **salinan terpisah** dengan ikon
  di-inline manual (bukan hasil render `index.html` yang sebenarnya) supaya bisa
  jalan tanpa CDN. Sudah disetujui tampilannya, tapi tetap perlu 1x pengecekan
  manual di browser nyata (buka `index.html` langsung) sebelum merge ke `main`,
  untuk memastikan Tailwind/Chart.js/Lucide dari CDN asli benar-benar termuat
  dan tidak ada perbedaan visual dari artifact preview.

## 2. Ikon Lucide masih pakai `unpkg.com/lucide@latest` (unpinned)

Pre-existing dari sebelum sesi ini, tidak diperbaiki: `index.html` masih memuat
`https://unpkg.com/lucide@latest` — versi tidak di-pin, jadi tampilan ikon bisa
berubah sewaktu-waktu tanpa peringatan kalau lucide merilis versi baru dengan
perubahan breaking. Chart.js (`cdn.jsdelivr.net/npm/chart.js`) juga sama,
tidak di-pin versi.

Rekomendasi: pin ke versi spesifik untuk kedua CDN ini di sesi berikutnya.

## 3. Data Pati (Tab 1 — Market Value & Crop) tidak lengkap

- Hanya Padi & Bawang Merah yang punya angka Ha untuk Pati (dari sheet
  beluk/ulat bawang di Excel). Jagung, Cabai, Kentang diisi `0` dengan badge
  "Data belum lengkap" di kartu komoditas — **bukan representasi nyata**,
  hanya penanda gap data.
- Total Market Value & breakdown pestisida untuk territory "Pati" di Tab 1
  akan under-counted selama data 3 komoditas itu belum diisi lewat folder
  `input/`.

## 4. Template CSV di folder `input/` sudah usang (stale)

> ✅ DITUTUP 11 Sep — Template lama dihapus. Penggantinya `data_csv.py` — export/import CSV yang mengikuti skema nyata (200 baris hama/penyakit, 36 baris luas panen, 5 agregat), dengan uji bolak-balik supaya tidak ada angka hilang di jalan.

Template `luas_panen_template.csv`, `parameter_biaya_template.csv`, dan
`beluk_template.csv` dibuat di sesi sebelumnya untuk struktur data lama
(single beluk table). Skema `datasetHamaPenyakit` yang baru jauh lebih kaya
(breakdown bulanan Jan–Des + top-5 produk per 13 kombinasi komoditas/hama-
penyakit) dan **belum ada template CSV yang mencerminkan skema baru ini**.
Kalau ada update data hama/penyakit baru, formatnya harus disamakan manual
dengan struktur `datasetHamaPenyakit` di `index.html`, bukan lewat template
yang ada sekarang.

## 5. Gap data product share (5 dari 13 kombinasi tidak punya data produk)

Tidak ada data top-5 produk market leader untuk:
- Kentang: Busuk Daun, Bercak Kering, Busuk Umbi, Layu Bakteri
- Cabai: Patek Buah / Antraknosa

Ditampilkan sebagai "Data belum tersedia" di tabel & chart product share.
Ini gap data asli dari file Excel yang di-upload, bukan bug — perlu dilengkapi
manual kalau datanya sudah ada.

## 6. Konsistensi format angka `area` antar dataset

- Di `datasetTerritory` (Tab 1), Ha untuk sub-territory Pati sudah dibulatkan
  ke integer (mis. `102551`).
- Di `datasetHamaPenyakit` (Tab 2), row Pati yang sama masih menyimpan angka
  asli dari Excel apa adanya (`102551.3`) — tabel di-tampilkan sudah dibulatkan
  saat render (`Math.round`), tapi nilai mentah di dua dataset ini **tidak
  identik**. Belum ada satu sumber kebenaran (single source of truth) untuk
  luas area per district.

## 7. Agregasi "Product Share" tidak dinormalisasi ke 100%

`computeAggregatedProducts()` menghitung rata-rata tertimbang share per produk
dari seluruh district yang tampil, tapi karena tiap district punya top-5
produk yang berbeda-beda, total seluruh produk pada chart **tidak selalu
berjumlah 100%**. Ini valid secara matematis (rata-rata tertimbang, bukan
komposisi), tapi berpotensi membingungkan user yang mengharapkan pie/bar chart
biasa yang selalu total 100%. Perlu keputusan desain: beri keterangan di UI,
atau ubah metodologi agregasi.

## 8. Pencocokan nama produk berbasis string exact-match

Ranking top produk (baik di kartu overview maupun chart product share)
mencocokkan nama produk secara string persis. Kalau ada variasi penulisan di
sumber data Excel (mis. "Virtako 300SC" vs "Virtako 300 SC"), keduanya akan
dihitung sebagai produk berbeda dan memecah share-nya. Belum ada normalisasi/
fuzzy-matching nama produk.

## 9. Pola filter "Semua Sub X" berbasis string prefix

`activeSubTerritory.startsWith("Semua Sub")` dipakai di banyak tempat sebagai
penanda "semua sub-territory dipilih". Ini konvensi string, bukan flag boolean
eksplisit — rawan salah kalau ada label sub-territory baru yang kebetulan juga
diawali "Semua Sub" tapi bukan dimaksudkan sebagai wildcard. Berfungsi untuk
sekarang, tapi sebaiknya di-refactor jadi flag terpisah (mis.
`activeSubTerritory === null` untuk "semua") kalau struktur data terus tumbuh.

## 10. Belum ada dokumentasi skema data untuk kontributor berikutnya

> ✅ DITUTUP 11 Sep — `SKEMA.md` di akar repo: struktur kedua berkas data + cara menambah wilayah/hama/komoditas.

Tidak ada README/CLAUDE.md yang menjelaskan struktur `datasetHamaPenyakit`
(bagaimana menambah komoditas baru, hama/penyakit baru, atau territory baru).
Pola saat ini harus dipelajari langsung dari kode `index.html`. Perlu
ditambahkan sebelum tim lain ikut mengembangkan section ini.

## 11. Tidak ada automated test / CI

Validasi sesi ini seluruhnya manual (skrip Node ad-hoc di `/tmp`, tidak
disimpan ke repo). Tidak ada test suite atau CI check yang jalan otomatis di
PR untuk mendeteksi regresi di kalkulasi (mis. rata-rata tertimbang, agregasi
produk) kalau ada yang mengubah data atau logic di kemudian hari.

## 12. Grafik Tab 1 kosong saat halaman pertama dibuka

Ditemukan 11 Sep waktu merender `index.html` di browser sungguhan (butir #1).

`cropMarketChart` dan `pesticideSplitChart` tampil kosong — sumbu 0–1.0 tanpa batang, pie tanpa
irisan — padahal kartu statistik di atasnya menampilkan angka yang benar (Rp 2,67 Triliun dst).

**Akarnya**, di penangan `DOMContentLoaded`: `updateDashboardData()` dipanggil **sebelum**
`initCharts()`. `updateDashboardData()` memanggil `updateCharts()`, tapi saat itu objek grafiknya
belum ada, jadi pengaman `if (!cropMarketChart) return;` langsung keluar tanpa bersuara. Sesudahnya
`initCharts()` membuat grafik dengan data nol, dan tidak ada yang memperbaruinya lagi.

Akibatnya grafik baru terisi setelah pengguna menekan salah satu tombol filter. Tab 2 tidak kena
karena `updateHamaPenyakitView()` memang dipanggil setelah `initCharts()`.

Perbaikannya satu baris — pindahkan `initCharts()` ke atas `updateDashboardData()`.
Dikerjakan di Section 2, supaya Section 1 murni pemindahan tempat tanpa perubahan perilaku.

## 13. Angka turunan di "Semua JT" tidak ikut terhitung ulang

`totalMv`, `insec`, `fung`, `herb` di entri `"Semua JT"` adalah hasil hitungan `ha × cost` yang
disimpan. Kalau `ha` atau `cost` diubah, keempatnya tidak ikut berubah — harus disesuaikan manual
lewat `agregat_jateng.csv`. Sebaiknya dihitung `build.py` saja, bukan disimpan.
