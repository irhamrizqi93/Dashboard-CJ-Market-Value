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


def _import_luas(d) -> int:
    per_t = {t['name']: t for t in d}
    n = 0
    for r in _baca('luas_panen.csv'):
        t = per_t.get(r['territory'])
        if not t or 'subData' not in t:
            sys.exit(f"❌ territory '{r['territory']}' tak dikenal di data/market.json")
        t['subData'][r['sub_territory']] = {k: _angka(r[f'{k}_ha']) for k in KOMODITAS}
        n += 1
    return n


# ─────────────────────────── agregat se-Jawa Tengah & DIY ───────────────────────────

KOL_AGG = ['komoditas', 'ha', 'cost_per_ha_idr', 'total_mv', 'insektisida', 'fungisida', 'herbisida']
_FIELD = {'ha': 'ha', 'cost_per_ha_idr': 'cost', 'total_mv': 'totalMv',
          'insektisida': 'insec', 'fungisida': 'fung', 'herbisida': 'herb'}


def _export_agg(d) -> Path:
    jt = next(t for t in d if 'crops' in t)
    baris = [dict({'komoditas': k}, **{kol: jt['crops'][k][f] for kol, f in _FIELD.items()})
             for k in KOMODITAS if k in jt['crops']]
    return _tulis('agregat_jateng.csv', KOL_AGG, baris)


def _import_agg(d) -> int:
    jt = next(t for t in d if 'crops' in t)
    for r in _baca('agregat_jateng.csv'):
        c = jt['crops'].get(r['komoditas'])
        if c is None:
            sys.exit(f"❌ komoditas '{r['komoditas']}' tak dikenal di 'Semua JT'")
        c.update({f: _angka(r[kol], bulat=True) for kol, f in _FIELD.items()})
    return len(jt['crops'])


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


def _import_hp() -> tuple[dict, int]:
    d: dict = {}
    n = 0
    for r in _baca('hama_penyakit.csv'):
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


def impor() -> None:
    d = _muat(MARKET)
    n_luas, n_agg = _import_luas(d), _import_agg(d)
    h, n_hp = _import_hp()
    _simpan(MARKET, d)
    _simpan(HAMA, h)
    print(f'✅ import selesai — {n_luas} baris luas panen · {n_agg} komoditas agregat · {n_hp} baris hama/penyakit')
    print('   Lanjut: python3 build.py')


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
        print('✅ selftest OK — data utuh setelah export→import (nol angka hilang/berubah)')
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
