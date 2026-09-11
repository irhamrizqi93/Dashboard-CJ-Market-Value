# Folder `input/` — bahan mentah & lembar kerja

Isi folder ini **bukan** yang dibaca dashboard. Yang dibaca dashboard adalah `data/*.json`.

Folder ini dua gunanya:

1. **Arsip berkas mentah** dari lapangan/survey (Excel, CSV apa adanya) — disimpan supaya
   asal-usul angkanya bisa ditelusuri. Contoh: `estimasi serangan hama penyakit rice horti dan pestisida.xlsx`.
2. **Lembar kerja CSV** hasil `data_csv.py export`, untuk menyunting data lewat Excel.
   CSV ini **sengaja tidak di-commit** (lihat `.gitignore`) — kalau ikut disimpan, lama-lama
   isinya berbeda dari `data/*.json` dan tidak ada yang tahu mana yang benar.

## Cara memperbarui data

```bash
python3 data_csv.py export     # data/*.json  →  input/*.csv
# buka input/*.csv di Excel, sunting, simpan sebagai CSV lagi
python3 data_csv.py import     # input/*.csv  →  data/*.json
python3 build.py               # tanam ke index.html
python3 build.py --check       # pastikan sinkron
```

Lalu buka `index.html` di browser dan pastikan angkanya berubah seperti yang kamu harapkan,
sebelum commit.

## Tiga lembar kerjanya

| Berkas | Isi | Jumlah baris |
|---|---|---|
| `luas_panen.csv` | Luas panen 5 komoditas per kabupaten/kota | 36 |
| `agregat_jateng.csv` | Angka se-Jawa Tengah & DIY per komoditas: luas, biaya per Ha, nilai pasar | 5 |
| `hama_penyakit.csv` | Serangan hama/penyakit per kabupaten + pola bulanan + top-5 produk | 200 |

Penjelasan tiap kolom → [`../SKEMA.md`](../SKEMA.md).

## Yang perlu diperhatikan

- **Jangan menambah kolom** di CSV. Kolom yang tidak dikenal diabaikan saat impor.
- **Kolom kosong dianggap 0.** Kalau datanya memang belum ada, biarkan kosong — jangan diisi
  tebakan. Dashboard sudah punya penanda "Data belum tersedia" untuk kasus itu.
- **Baris produk yang kosong tetap kosong.** Kalau kelima kolom `produkN_nama` kosong, dashboard
  menampilkan "Data belum tersedia" — itu memang disengaja, bukan kerusakan.
- **Territory baru** tidak bisa ditambah lewat CSV; itu mengubah struktur. Lihat `SKEMA.md`.
