# SKEMA — struktur data dashboard

> Dibuat 2026-09-11. Menutup `tech_debt.md` #10 (dulu strukturnya cuma bisa dipelajari dengan
> membaca `index.html`).

Dashboard ini statis: tidak ada server, tidak ada database. Datanya hidup di dua berkas JSON,
lalu ditanam ke `index.html` oleh `build.py`.

```
input/mentah/YYYY-MM_*.xlsx   (arsip — tak pernah dibaca dashboard)
      │
      ▼  disunting lewat Excel: data_csv.py export → edit → import (divalidasi)
data/market.json + data/hama_penyakit.json     ← SUMBER KEBENARAN
data/_sumber.json                              ← kapan datanya, dari mana
      │
      ▼  build.py
index.html   blok data  <<<DATA>>> … <<</DATA>>>
             kaki halaman <<<SUMBER>>> … <<</SUMBER>>>
```

Satu perintah untuk memeriksa semuanya: **`python3 periksa.py`**.

**Jangan pernah menyunting angka langsung di `index.html`.** Blok itu ditimpa setiap
`build.py` jalan. `build.py --check` akan gagal kalau keduanya tidak sinkron.

---

## `data/_sumber.json` — asal-usul data

Bukan angka, tapi **wajib** ikut diperbarui tiap kali data berubah. Isinya tampil di kaki
halaman dashboard, supaya orang yang menerima tautan/tangkapan layarnya tahu angkanya per kapan.

| Kolom | Guna |
|---|---|
| `versi` | penanda singkat, mis. `2026-09` |
| `tanggal_data` | `YYYY-MM-DD`. Tanggal **datanya**, bukan tanggal kamu menyuntingnya |
| `sifat` | `estimasi` → dashboard memasang peringatan kuning otomatis |
| `sumber` | dari survey/berkas apa; sebut nama berkas di `input/mentah/` |
| `cakupan` | ringkas: berapa territory, komoditas, baris |
| `catatan` | apa yang belum lengkap — isi jujur |
| `riwayat` | satu baris tiap pembaruan: versi, tanggal, apa yang berubah |

`periksa.py` menolak kalau `versi`, `tanggal_data`, `sumber`, atau `cakupan` kosong.

## `data/market.json` — Tab 1 (Market Value & Crop)

Larik berisi 8 entri: 1 agregat + 7 territory.

**Entri agregat** (`name: "Semua JT"`) — satu-satunya yang punya `crops`:

```json
{
  "name": "Semua JT",
  "label": "Semua Jawa Tengah & DIY",
  "subTerritories": ["Semua Kab/Kota"],
  "crops": {
    "padi": { "ha": 1650000, "cost": 900000, "totalMv": 1485000000000,
              "insec": 594000000000, "fung": 445500000000, "herb": 445500000000 }
  }
}
```

| Kolom | Arti |
|---|---|
| `ha` | luas panen (hektar) |
| `cost` | biaya pestisida per hektar (Rupiah) |
| `totalMv` | nilai pasar = `ha × cost` |
| `insec` / `fung` / `herb` | pecahan nilai pasar ke insektisida / fungisida / herbisida |

⚠️ `totalMv`, `insec`, `fung`, `herb` itu **hasil hitungan yang disimpan**, bukan angka mandiri.
Kalau `ha` atau `cost` diubah, keempatnya **tidak ikut berubah sendiri** — harus disesuaikan
manual lewat `agregat_jateng.csv`. Ini utang yang diketahui.

**Entri territory** (7 sisanya) — punya `subData`, tanpa `crops`:

```json
{
  "name": "Brebes",
  "label": "Brebes (Pantura & Horti)",
  "subTerritories": ["Semua Sub Brebes", "Kab. Brebes", "Kab. Tegal", "Kota Tegal", "Purbalingga Atas"],
  "incompleteCrops": ["jagung", "cabai", "kentang"],
  "subData": { "Kab. Brebes": { "padi": 68000, "jagung": 12000, "bawang": 32000, "cabai": 4500, "kentang": 500 } }
}
```

- `subTerritories` — daftar tombol filter. Entri pertama **wajib** diawali `"Semua Sub "`;
  string itulah yang dipakai kode sebagai penanda "semua sub dipilih".
- `subData` — luas panen per kabupaten/kota, satuan hektar. Kuncinya harus ada di `subTerritories`.
- `incompleteCrops` — *opsional*. Daftar komoditas yang datanya belum lengkap; dashboard memasang
  badge "Data belum lengkap". Isi jujur, jangan diisi angka tebakan.

## `data/hama_penyakit.json` — Tab 2 (Hama, Penyakit & Product Share)

Objek bersarang tiga lapis: **komoditas → hama/penyakit → baris per kabupaten**.

```json
{
  "padi": {
    "label": "Padi",
    "icon": "🌾",
    "hamaPenyakit": {
      "beluk": {
        "label": "Beluk (Penggerek Batang)",
        "type": "hama",
        "productLabel": "Insektisida",
        "rows": [ { "…": "lihat tabel di bawah" } ]
      }
    }
  }
}
```

| Kolom baris | Arti |
|---|---|
| `territory` / `subTerritory` | wilayah; `territory` harus sama dengan `name` di `market.json` |
| `district` | daftar kecamatan, teks bebas dipisah koma — tampilan saja |
| `area` | luas komoditas itu di wilayah tersebut (hektar) |
| `attackPct` | porsi luas yang terserang, **pecahan** (`0.145` = 14,5%) |
| `severityPct` | tingkat keparahan, pecahan |
| `risk` | `"Rendah"` · `"Sedang"` · `"Tinggi"` — teks persis, dipakai untuk warna |
| `monthly` | **tepat 12 angka**, Januari–Desember, pecahan |
| `products` | 5 produk market leader, atau `null` |

⚠️ **`products` harus `null`, bukan `[]`, kalau datanya belum ada.** Kode memakai
`if (!r.products)` untuk menampilkan "Data belum tersedia" — dan array kosong di JavaScript
bernilai *truthy*, jadi `[]` akan lolos dari pengaman itu dan memunculkan baris kosong.

`type` menentukan ikon (`hama` vs `penyakit`); `productLabel` jadi judul kolom
("Top 5 **Insektisida** Market Leader").

---

## Menambah sesuatu yang baru

**Kabupaten baru** → cukup lewat CSV: tambah baris di `luas_panen.csv`, dan tambahkan namanya
ke `subTerritories` territory yang bersangkutan di `data/market.json`.

**Hama/penyakit baru** → tambah baris di `hama_penyakit.csv` dengan `hp_key` baru
(huruf kecil, tanpa spasi) beserta `hp_label`, `hp_type`, `hp_product_label`. Tombolnya muncul
sendiri — `renderHpButtons()` membacanya dari data.

**Komoditas baru** → tidak cukup lewat data. Kode Tab 1 menyebut lima komoditas secara eksplisit
(`crops.padi`, `crops.jagung`, …) di beberapa tempat, termasuk `updateCharts()`. Menambah
komoditas keenam berarti menyunting `index.html` juga.

**Territory baru** → tambah entri di `data/market.json` lengkap dengan `subTerritories` +
`subData`. Tombolnya ikut muncul sendiri.

---

## Setelah mengubah apa pun

```bash
python3 build.py       # tanam ke index.html
python3 periksa.py     # periksa semuanya sekaligus — hijau baru boleh commit
```
Lalu **buka `index.html` di browser** dan lihat angkanya. Pemeriksa otomatis cuma memastikan
datanya tidak hilang di jalan dan bentuknya masuk akal — dia tidak tahu angkanya benar atau tidak.
