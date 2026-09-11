# Dashboard Pertanian & Market CJ — Jawa Tengah & DIY

Dashboard statis satu berkas: luas panen 5 komoditas, perkiraan nilai pasar pestisida, dan
analisa serangan hama/penyakit per kabupaten — lengkap dengan pola bulanan dan produk yang
memimpin pasar.

Tidak ada server, tidak ada database. Buka `index.html` di browser, selesai.

## ⚠️ Sifat angkanya

**Nilai pasar di sini model, bukan pengukuran.** Rumusnya:

```
nilai pasar = luas panen (ha) × biaya pestisida per hektar × porsi segmen
```

Biaya per hektar adalah **asumsi**, bukan belanja yang pernah diukur. Kalau asumsi itu meleset
30%, seluruh nilai pasarnya ikut meleset 30% — dan tidak ada tanda apa pun di angkanya. Kaki
halaman dashboard sudah mencantumkan peringatan ini; jangan dibuang saat meneruskan gambarnya.

Data serangan hama/penyakit juga **estimasi/survey**, bukan sensus.

## Struktur

```
data/market.json          luas panen per kabupaten + parameter biaya   ← SUMBER KEBENARAN
data/hama_penyakit.json   200 baris serangan + pola bulanan + top-5 produk
data/_sumber.json         kapan datanya, dari mana, apa yang belum lengkap
data/alias_produk.json    penyeragaman nama produk

index.html                tampilan. Blok datanya HASIL GENERATE — jangan disunting langsung
build.py                  data/*.json  →  index.html
data_csv.py               data/*.json  ⇄  input/*.csv   (sunting lewat Excel)
periksa.py                satu perintah, memeriksa semuanya

input/mentah/             arsip berkas mentah, pola nama YYYY-MM_keterangan.xlsx
SKEMA.md                  penjelasan tiap kolom + cara menambah wilayah/hama/komoditas
tech_debt.md              yang masih menggantung, apa adanya
```

## Memperbarui data

```bash
# 1. simpan berkas mentahnya
#    input/mentah/2026-10_nama-survey.xlsx

python3 data_csv.py export     # data/*.json  →  input/*.csv
# 2. sunting input/*.csv di Excel, simpan sebagai CSV lagi
python3 data_csv.py import     # ditolak kalau ada yang janggal

# 3. perbarui data/_sumber.json — tanggal data, versi, sumbernya
python3 build.py               # tanam ke index.html + kaki halaman
python3 periksa.py             # ← hijau baru commit
```

Impor bersifat **semua-atau-tidak-sama-sekali**: satu baris janggal → seluruh impor dibatalkan
dan nol berkas berubah. Yang paling sering tertangkap: persen ditulis `14.5` padahal formatnya
pecahan (`0.145`).

`periksa.py` memeriksa JSON masih sah · jejak sumber terisi · isi data cocok satu sama lain ·
jalur CSV utuh bolak-balik · `index.html` sinkron dengan `data/`. Yang **tidak** diperiksa:
apakah angkanya benar. Itu tetap tugas mata manusia — buka `index.html` dan lihat.

## Yang belum ada datanya

- **Kota Pekalongan · Kota Semarang · Kota Surakarta · Kota Magelang** — belum ada sama sekali.
- **Pati** — jagung, cabai, kentang belum berangka.
- **Data produk market leader** — belum ada untuk kentang (busuk daun, bercak kering, busuk umbi,
  layu bakteri) dan cabai (patek/antraknosa). Total 53 dari 200 baris.

⚠️ Angka **0** tidak selalu berarti data hilang. Kentang bernilai 0 di kabupaten dataran rendah
memang benar — kentang tidak ditanam di sana.

## Dua angka luas yang tidak sepakat

Data ini memuat dua angka luas yang berbeda untuk hal yang sama:

| Komoditas | Agregat "se-wilayah" | Jumlah per kabupaten | Selisih |
|---|---|---|---|
| padi | 1.650.000 | 1.875.553 | +13,7% |
| jagung | 550.000 | 604.200 | +9,9% |
| bawang | 58.000 | 71.450 | +23,2% |
| cabai | 45.000 | 70.350 | **+56,3%** |
| kentang | 18.000 | 18.200 | +1,1% |

Judul besar di dashboard memakai **angka agregat**. Belum ada yang memastikan mana yang benar,
jadi keduanya dibiarkan apa adanya — tapi perlu diketahui kalau ada yang menjumlah sendiri
angka per kabupaten dan mendapat hasil berbeda.

## Catatan teknis

- Pustaka luar (Tailwind, Chart.js, Lucide) **di-pin ke versi tertentu**. Jangan dikembalikan ke
  `@latest` — versi yang berubah sendiri bisa mengubah tampilan tanpa ada yang menyentuh kode.
- `index.html` sengaja **memuat datanya di dalam berkas** (bukan `fetch`) supaya masih bisa dibuka
  dengan klik-ganda dari komputer; `fetch` dari `file://` diblokir browser.
- `input/*.csv` tidak di-commit — itu lembar kerja sementara. Sumber kebenaran tetap `data/*.json`.
