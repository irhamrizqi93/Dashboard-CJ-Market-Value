# Folder Input Data

Taruh file raw data (hasil update lapangan / survey) di sini sebagai referensi
sebelum datanya dipindahkan ke dataset di dalam `index.html`.

Dashboard ini adalah single-file HTML statis — semua data (`datasetTerritory`
dan `datasetBeluk`) hardcode di bagian `<script>` pada `index.html`. Folder
ini **tidak otomatis terbaca** oleh dashboard; tujuannya hanya sebagai tempat
penyimpanan raw data mentah yang rapi sebelum di-input manual (atau lewat
bantuan Claude) ke `index.html`.

## Template yang tersedia

- `luas_panen_template.csv` — data luas panen per komoditas, per
  territory/sub-territory (Ha). Dipakai untuk mengisi `datasetTerritory`.
- `parameter_biaya_template.csv` — biaya pestisida per Ha dan porsi alokasi
  insektisida/fungisida/herbisida per komoditas.
- `beluk_template.csv` — data serangan hama beluk per district (luas padi,
  % serangan, % keparahan, tingkat risiko, top 5 produk insektisida).

Setiap template sudah berisi baris contoh (ditandai `CONTOH`) yang meniru
data yang saat ini ada di `index.html`. Hapus baris contoh, isi baris baru
sesuai data terbaru, lalu simpan file mentahnya di folder ini (boleh
ditambah versi/tanggal, misal `luas_panen_2026_09.csv`).

## Alur update

1. Taruh/update file CSV raw data di folder `input/`.
2. Minta Claude (atau update manual) untuk memasukkan data dari file
   tersebut ke `datasetTerritory` / `datasetBeluk` di `index.html`.
3. Commit perubahan `index.html` beserta file raw data barunya.
