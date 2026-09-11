#!/usr/bin/env python3
"""data_csv.py — jembatan CSV ⇄ data/*.json, supaya data bisa diperbarui lewat Excel.

Alurnya:

    python3 data_csv.py export     data/*.json  →  input/*.csv   (buka & sunting di Excel)
    python3 data_csv.py import     input/*.csv  →  data/*.json
    python3 build.py                             tanam ke index.html

`data/*.json` tetap satu-satunya sumber kebenaran. CSV itu cuma jendela kerja — sengaja
TIDAK di-commit (lihat .gitignore), supaya tidak lahir dua daftar yang lama-lama berbeda.

Impor bersifat MENAMBAL, bukan menimpa: kolom yang tidak ada di CSV (mis. `totalMv`
yang sudah terhitung di "Semua JT") dibiarkan apa adanya.

Uji: python3 data_csv.py --selftest   (export → import → data harus persis sama)
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARKET = ROOT / 'data' / 'market.json'
HAMA = ROOT / 'data' / 'hama_penyakit.json'
INPUT = ROOT / 'input'
KOMODITAS = ['padi', 'jagung', 'bawang', 'cabai', 'kentang']
BULAN = [f'm{i:02d}' for i in range(1, 13)]


def _muat(p: Path):
    return json.loads(p.read_text(encoding='utf-8'))


def _simpan(p: Path, obj) -> None:
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _tulis(nama: str, kolom: list[str], baris: list[dict]) -> Path:
    INPUT.mkdir(exist_ok=True)
    p = INPUT / nama
    with p.open('w', newline='', encoding='utf-8-sig') as f:   # utf-8-sig: Excel baca emoji/é benar
        w = csv.DictWriter(f, fieldnames=kolom)
        w.writeheader()
        w.writerows(baris)
    return p


def _baca(nama: str) -> list[dict]:
    p = INPUT / nama
    if not p.exists():
        sys.exit(f'❌ {p.relative_to(ROOT)} tak ada. Jalankan dulu: python3 data_csv.py export')
    with p.open(newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def _angka(s: str, bulat: bool = False):
    """String CSV → angka. Kosong = 0. Excel kadang menulis '1.234,5' atau '12%'."""
    s = (s or '').strip().replace('%', '')
    if not s:
        return 0
    n = float(s.replace(',', '.') if s.count(',') == 1 and '.' not in s else s.replace(',', ''))
    return int(n) if bulat or n == int(n) else n


# ─────────────────────────── luas panen (per sub-territory) ───────────────────────────

def _export_luas(d) -> Path:
    baris = [dict({'territory': t['name'], 'sub_territory': sub},
                  **{f'{k}_ha': v.get(k, 0) for k in KOMODITAS})
             for t in d if 'subData' in t for sub, v in t['subData'].items()]
    return _tulis('luas_panen.csv', ['territory', 'sub_territory'] + [f'{k}_ha' for k in KOMODITAS], baris)


def _import_luas(d, baris) -> int:
    per_t = {t['name']: t for t in d}
    for r in baris:
        per_t[r['territory']]['subData'][r['sub_territory']] = {
            k: _angka(r[f'{k}_ha']) for k in KOMODITAS}
    return len(baris)


# ─────────────────────────── agregat se-Jawa Tengah & DIY ───────────────────────────

KOL_AGG = ['komoditas', 'ha', 'cost_per_ha_idr', 'total_mv', 'insektisida', 'fungisida', 'herbisida']
_FIELD = {'ha': 'ha', 'cost_per_ha_idr': 'cost', 'total_mv': 'totalMv',
          'insektisida': 'insec', 'fungisida': 'fung', 'herbisida': 'herb'}


def _export_agg(d) -> Path:
    jt = next(t for t in d if 'crops' in t)
    baris = [dict({'komoditas': k}, **{kol: jt['crops'][k][f] for kol, f in _FIELD.items()})
             for k in KOMODITAS if k in jt['crops']]
    return _tulis('agregat_jateng.csv', KOL_AGG, baris)


def _import_agg(d, baris) -> int:
    jt = next(t for t in d if 'crops' in t)
    for r in baris:
        jt['crops'][r['komoditas']].update(
            {f: _angka(r[kol], bulat=True) for kol, f in _FIELD.items()})
    return len(baris)


# ─────────────────────────── hama & penyakit (200 baris) ───────────────────────────

KOL_HP = (['komoditas', 'komoditas_label', 'komoditas_icon', 'hp_key', 'hp_label', 'hp_type',
           'hp_product_label', 'territory', 'sub_territory', 'district', 'area_ha',
           'attack_pct', 'severity_pct', 'risiko'] + BULAN
          + [f'produk{i}_{x}' for i in range(1, 6) for x in ('nama', 'pct')])


def _export_hp(d) -> Path:
    baris = []
    for kom, v in d.items():
        for hk, hp in v['hamaPenyakit'].items():
            for r in hp['rows']:
                b = {'komoditas': kom, 'komoditas_label': v['label'], 'komoditas_icon': v['icon'],
                     'hp_key': hk, 'hp_label': hp['label'], 'hp_type': hp['type'],
                     'hp_product_label': hp['productLabel'], 'territory': r['territory'],
                     'sub_territory': r['subTerritory'], 'district': r['district'],
                     'area_ha': r['area'], 'attack_pct': r['attackPct'],
                     'severity_pct': r['severityPct'], 'risiko': r['risk']}
                b.update(dict(zip(BULAN, r['monthly'])))
                produk = r.get('products') or []      # sebagian baris memang null (gap data)
                for i in range(5):
                    p = produk[i] if i < len(produk) else None
                    b[f'produk{i+1}_nama'] = p['name'] if p else ''
                    b[f'produk{i+1}_pct'] = p['pct'] if p else ''
                baris.append(b)
    return _tulis('hama_penyakit.csv', KOL_HP, baris)


def _import_hp(baris) -> tuple[dict, int]:
    d: dict = {}
    n = 0
    for r in baris:
        kom = d.setdefault(r['komoditas'], {'label': r['komoditas_label'],
                                            'icon': r['komoditas_icon'], 'hamaPenyakit': {}})
        hp = kom['hamaPenyakit'].setdefault(r['hp_key'], {
            'label': r['hp_label'], 'type': r['hp_type'],
            'productLabel': r['hp_product_label'], 'rows': []})
        produk = [{'name': r[f'produk{i}_nama'].strip(), 'pct': _angka(r[f'produk{i}_pct'])}
                  for i in range(1, 6) if r[f'produk{i}_nama'].strip()]
        hp['rows'].append({'territory': r['territory'], 'subTerritory': r['sub_territory'],
                           'district': r['district'], 'area': _angka(r['area_ha']),
                           'attackPct': _angka(r['attack_pct']),
                           'severityPct': _angka(r['severity_pct']), 'risk': r['risiko'],
                           'monthly': [_angka(r[b]) for b in BULAN],
                           # null, BUKAN []: index.html pakai `if (!r.products)` untuk
                           # menampilkan "Data belum tersedia" — array kosong itu truthy,
                           # jadi [] akan melewati pengaman itu dan menampilkan baris kosong.
                           'products': produk or None})
        n += 1
    return d, n


# ─────────────────────────────────── perintah ───────────────────────────────────

def ekspor() -> None:
    d, h = _muat(MARKET), _muat(HAMA)
    for p in (_export_luas(d), _export_agg(d), _export_hp(h)):
        print(f'  → {p.relative_to(ROOT)}')
    print('✅ export selesai. Sunting di Excel, lalu: python3 data_csv.py import')


# ─────────────────────────────────── pemeriksaan ───────────────────────────────────

RISIKO = ('Rendah', 'Sedang', 'Tinggi')


def _validasi(d, luas, agg, hp) -> list[str]:
    """Periksa SEMUA baris CSV sebelum satu berkas pun ditulis.

    Kenapa keras: Excel gampang membuat kesalahan yang tidak kelihatan. Yang paling sering
    adalah menulis `14.5` untuk 14,5% padahal formatnya pecahan (`0.145`) — dashboard lalu
    menampilkan serangan 1450% tanpa ada yang menahan. Semua masalah dikumpulkan dulu lalu
    dilaporkan sekaligus, supaya tidak betulkan-satu-jalankan-lagi berkali-kali.
    """
    galat: list[str] = []
    per_t = {x['name']: x for x in d}
    sub_sah = {x['name']: set(x.get('subTerritories', [])) for x in d}
    jt = next((x for x in d if 'crops' in x), {'crops': {}})

    def angka(r, kol, no, berkas, maks=None):
        mentah = (r.get(kol) or '').strip()
        try:
            n = _angka(mentah)
        except ValueError:
            galat.append(f'{berkas} baris {no}: kolom `{kol}` bukan angka → {mentah!r}')
            return None
        if n < 0:
            galat.append(f'{berkas} baris {no}: kolom `{kol}` negatif ({n})')
        elif maks is not None and n > maks:
            galat.append(f'{berkas} baris {no}: kolom `{kol}` = {n}, di luar 0–{maks}. '
                         'Pecahan ditulis 0,145 untuk 14,5% — bukan 14,5')
        return n

    for no, r in enumerate(luas, 2):                       # baris 1 = judul kolom
        wil = (r.get('territory') or '').strip()
        sub = (r.get('sub_territory') or '').strip()
        if wil not in per_t or 'subData' not in per_t[wil]:
            galat.append(f"luas_panen.csv baris {no}: territory '{wil}' tak dikenal di data/market.json")
        elif sub and sub not in sub_sah[wil]:
            galat.append(f"luas_panen.csv baris {no}: '{sub}' belum terdaftar di subTerritories "
                         f"territory '{wil}' — tombol filternya tak akan muncul. "
                         'Tambahkan dulu di data/market.json (lihat SKEMA.md)')
        for k in KOMODITAS:
            angka(r, f'{k}_ha', no, 'luas_panen.csv')

    for no, r in enumerate(agg, 2):
        kom = (r.get('komoditas') or '').strip()
        if kom not in jt['crops']:
            galat.append(f"agregat_jateng.csv baris {no}: komoditas '{kom}' tak dikenal di 'Semua JT'")
        for kol in KOL_AGG[1:]:
            n = angka(r, kol, no, 'agregat_jateng.csv')
            if kol == 'cost_per_ha_idr' and n == 0:
                galat.append(f'agregat_jateng.csv baris {no}: biaya per hektar 0 — '
                             'nilai pasarnya pasti ikut nol')

    jenis: dict = {}
    for no, r in enumerate(hp, 2):
        kom, hk = (r.get('komoditas') or '').strip(), (r.get('hp_key') or '').strip()
        if not kom or not hk:
            galat.append(f'hama_penyakit.csv baris {no}: `komoditas` / `hp_key` tak boleh kosong')
            continue
        wil = (r.get('territory') or '').strip()
        if wil not in per_t or 'subData' not in per_t[wil]:
            galat.append(f"hama_penyakit.csv baris {no}: territory '{wil}' tak dikenal di data/market.json")
        if (r.get('risiko') or '').strip() not in RISIKO:
            galat.append(f"hama_penyakit.csv baris {no}: risiko '{r.get('risiko')}' "
                         f'tak sah — harus salah satu dari {", ".join(RISIKO)}')
        angka(r, 'area_ha', no, 'hama_penyakit.csv')
        for kol in ('attack_pct', 'severity_pct', *BULAN):
            angka(r, kol, no, 'hama_penyakit.csv', maks=1)
        for i in range(1, 6):
            nama = (r.get(f'produk{i}_nama') or '').strip()
            pct = (r.get(f'produk{i}_pct') or '').strip()
            if nama and not pct:
                galat.append(f'hama_penyakit.csv baris {no}: produk{i} ada namanya '
                             f'({nama}) tapi porsinya kosong')
            elif nama:
                angka(r, f'produk{i}_pct', no, 'hama_penyakit.csv', maks=1)
            elif pct:
                galat.append(f'hama_penyakit.csv baris {no}: produk{i} ada porsinya '
                             'tapi namanya kosong')
        # label satu hama/penyakit harus konsisten di semua barisnya, kalau tidak yang
        # terakhir menang diam-diam
        kunci = (kom, hk)
        label = (r.get('hp_label'), r.get('hp_type'), r.get('hp_product_label'))
        if kunci in jenis and jenis[kunci] != label:
            galat.append(f'hama_penyakit.csv baris {no}: label/tipe untuk {kom}/{hk} '
                         f'beda dari baris sebelumnya — {jenis[kunci]} vs {label}')
        jenis.setdefault(kunci, label)

    return galat


def impor() -> None:
    d = _muat(MARKET)
    luas, agg, hp = _baca('luas_panen.csv'), _baca('agregat_jateng.csv'), _baca('hama_penyakit.csv')
    galat = _validasi(d, luas, agg, hp)
    if galat:
        print(f'❌ IMPOR DIBATALKAN — {len(galat)} masalah ditemukan. NOL berkas diubah.\n')
        for g in galat[:30]:
            print('   •', g)
        if len(galat) > 30:
            print(f'   … dan {len(galat) - 30} lagi')
        print('\n   Betulkan di Excel, simpan, lalu jalankan lagi.')
        sys.exit(1)
    n_luas, n_agg = _import_luas(d, luas), _import_agg(d, agg)
    h, n_hp = _import_hp(hp)
    _simpan(MARKET, d)
    _simpan(HAMA, h)
    print(f'✅ import selesai — {n_luas} baris luas panen · {n_agg} komoditas agregat · {n_hp} baris hama/penyakit')
    print('   Lanjut: python3 build.py')


def _uji_tolak() -> None:
    """Buktikan pemeriksaan benar-benar menggigit — bukan sekadar ada.

    Tiap kasus di bawah ini pernah, atau gampang sekali, terjadi waktu menyunting di Excel.
    """
    d = _muat(MARKET)
    wil = next(x['name'] for x in d if 'subData' in x)
    sub = next(iter(next(x for x in d if x['name'] == wil)['subData']))
    dasar = {'komoditas': 'padi', 'komoditas_label': 'Padi', 'komoditas_icon': '🌾',
             'hp_key': 'beluk', 'hp_label': 'Beluk', 'hp_type': 'hama',
             'hp_product_label': 'Insektisida', 'territory': wil, 'sub_territory': sub,
             'district': 'A, B', 'area_ha': '1000', 'attack_pct': '0.1',
             'severity_pct': '0.2', 'risiko': 'Sedang',
             **{b: '0.05' for b in BULAN},
             **{f'produk{i}_{x}': '' for i in range(1, 6) for x in ('nama', 'pct')}}
    kasus = [
        ('persen ditulis 14.5 bukan 0.145', {'attack_pct': '14.5'}, 'di luar 0–1'),
        ('risiko tidak sah', {'risiko': 'Parah'}, 'tak sah'),
        ('territory asing', {'territory': 'Cirebon'}, 'tak dikenal'),
        ('angka bukan angka', {'area_ha': 'seribu'}, 'bukan angka'),
        ('luas negatif', {'area_ha': '-5'}, 'negatif'),
        ('produk ada nama tanpa porsi', {'produk1_nama': 'X 100 EC'}, 'porsinya kosong'),
        ('bulan di luar 0–1', {'m03': '3'}, 'di luar 0–1'),
    ]
    for nama, ubah, dicari in kasus:
        g = _validasi(d, [], [], [{**dasar, **ubah}])
        assert g, f'TIDAK TERDETEKSI: {nama}'
        assert any(dicari in x for x in g), f'pesan salah untuk {nama}: {g}'
    # label yang bentrok antar-baris untuk hama/penyakit yang sama
    g = _validasi(d, [], [], [dasar, {**dasar, 'hp_label': 'Beluk Lain'}])
    assert any('beda dari baris sebelumnya' in x for x in g), g
    # data yang benar TIDAK boleh ikut ditolak
    assert _validasi(d, [], [], [dasar]) == [], 'data sah malah ditolak'
    print(f'   ✔ {len(kasus) + 1} jenis data rusak tertangkap, data sah lolos')


def selftest() -> None:
    """Bolak-balik: data → CSV → data. Harus persis sama, kalau tidak ada yang hilang di jalan."""
    asli_m, asli_h = MARKET.read_text(encoding='utf-8'), HAMA.read_text(encoding='utf-8')
    simpan = {p: (INPUT / p).read_bytes() for p in ('luas_panen.csv', 'agregat_jateng.csv',
                                                   'hama_penyakit.csv') if (INPUT / p).exists()}
    try:
        ekspor()
        impor()
        m, h = MARKET.read_text(encoding='utf-8'), HAMA.read_text(encoding='utf-8')
        assert json.loads(m) == json.loads(asli_m), 'market.json berubah setelah bolak-balik CSV'
        assert json.loads(h) == json.loads(asli_h), 'hama_penyakit.json berubah setelah bolak-balik CSV'
        _uji_tolak()
        print('✅ selftest OK — data utuh setelah export→import, dan data rusak ditolak')
    finally:
        MARKET.write_text(asli_m, encoding='utf-8')
        HAMA.write_text(asli_h, encoding='utf-8')
        for p in ('luas_panen.csv', 'agregat_jateng.csv', 'hama_penyakit.csv'):
            (INPUT / p).unlink(missing_ok=True)
        for p, isi in simpan.items():
            (INPUT / p).write_bytes(isi)


if __name__ == '__main__':
    perintah = sys.argv[1] if len(sys.argv) > 1 else ''
    {'export': ekspor, 'import': impor, '--selftest': selftest}.get(
        perintah, lambda: sys.exit(__doc__))()
