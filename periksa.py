#!/usr/bin/env python3
"""periksa.py — satu perintah sebelum commit. Jalankan: python3 periksa.py

Menggantikan hafalan tiga perintah terpisah. Kalau ada yang merah, JANGAN commit.

Yang diperiksa:
  1. data/*.json masih JSON yang sah
  2. data/_sumber.json terisi — kapan datanya, dari mana
  3. isi data cocok satu sama lain — territory/sub-territory tidak menggantung,
     angka turunan masih sesuai bahannya, nama produk sudah seragam
  4. jalur CSV utuh bolak-balik, dan data rusak ditolak   (data_csv.py --selftest)
  5. index.html sinkron dengan data/                       (build.py --check)

Yang TIDAK diperiksa: apakah angkanya benar. Itu tetap tugas mata manusia —
buka index.html di browser dan lihat.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WAJIB_SUMBER = ('versi', 'tanggal_data', 'sumber', 'cakupan')
galat: list[str] = []


def bagian(judul: str) -> None:
    print(f'\n── {judul}')


def muat(nama: str):
    p = ROOT / 'data' / nama
    if not p.exists():
        galat.append(f'data/{nama} tidak ada')
        return None
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        galat.append(f'data/{nama} bukan JSON yang sah — baris {e.lineno}: {e.msg}')
        return None


def main() -> None:
    bagian('1–2. berkas data & jejak sumber')
    market, hama, sumber = muat('market.json'), muat('hama_penyakit.json'), muat('_sumber.json')
    if sumber:
        kosong = [k for k in WAJIB_SUMBER if not str(sumber.get(k, '')).strip()]
        if kosong:
            galat.append(f'data/_sumber.json belum diisi: {", ".join(kosong)}')
        else:
            print(f'   data per {sumber["tanggal_data"]} · versi {sumber["versi"]} '
                  f'· {sumber.get("sifat", "?")}')

    if market and hama:
        bagian('3. kecocokan antar-berkas')
        nama_t = {x['name'] for x in market}
        for x in market:
            for sub in x.get('subData', {}):
                if sub not in x.get('subTerritories', []):
                    galat.append(f"market.json: '{sub}' ada di subData {x['name']} tapi tidak di "
                                 'subTerritories — tombol filternya tak akan muncul')
        baris = 0
        for kom, v in hama.items():
            for hk, hp in v.get('hamaPenyakit', {}).items():
                for r in hp.get('rows', []):
                    baris += 1
                    if r.get('territory') not in nama_t:
                        galat.append(f"hama_penyakit.json {kom}/{hk}: territory "
                                     f"'{r.get('territory')}' tak ada di market.json")
                    if len(r.get('monthly') or []) != 12:
                        galat.append(f'hama_penyakit.json {kom}/{hk} / {r.get("subTerritory")}: '
                                     '`monthly` bukan 12 angka')
        # angka turunan: kalau `ha` atau `cost` diubah tanpa menyesuaikan sisanya, drift-nya
        # tidak kelihatan di mana pun — kartu statistik tetap tampil, cuma isinya salah
        jt = next((x for x in market if 'crops' in x), None)
        for kom, c in (jt or {}).get('crops', {}).items():
            if c['ha'] * c['cost'] != c['totalMv']:
                galat.append(f"market.json {kom}: totalMv {c['totalMv']:,} tidak sama dengan "
                             f"ha × cost ({c['ha'] * c['cost']:,}). Perbaiki lewat agregat_jateng.csv")
            if c['insec'] + c['fung'] + c['herb'] != c['totalMv']:
                galat.append(f"market.json {kom}: insec+fung+herb tidak berjumlah totalMv "
                             f"({c['insec'] + c['fung'] + c['herb']:,} vs {c['totalMv']:,})")

        # nama produk gaya lama yang lolos masuk akan memecah porsi pasar diam-diam
        pa = ROOT / 'data' / 'alias_produk.json'
        if pa.exists():
            peta = json.loads(pa.read_text(encoding='utf-8')).get('alias', {})
            lama = sorted({p2['name'] for v in hama.values()
                           for hp in v.get('hamaPenyakit', {}).values()
                           for r in hp.get('rows', []) for p2 in (r.get('products') or [])
                           if p2['name'] in peta})
            if lama:
                galat.append('nama produk gaya lama masih ada: ' + ', '.join(lama)
                             + ' — jalankan data_csv.py export lalu import')

        tanpa_produk = sum(1 for v in hama.values() for hp in v.get('hamaPenyakit', {}).values()
                           for r in hp.get('rows', []) if not r.get('products'))
        print(f'   {len(market) - 1} territory · {baris} baris hama/penyakit '
              f'({tanpa_produk} belum punya data produk)')

    for no, perintah, keterangan in [(4, ['data_csv.py', '--selftest'], 'jalur CSV'),
                                     (5, ['build.py', '--check'], 'index.html vs data/')]:
        bagian(f'{no}. {keterangan}')
        h = subprocess.run([sys.executable, *perintah], cwd=ROOT,
                           capture_output=True, text=True)
        for baris_keluar in (h.stdout + h.stderr).strip().splitlines():
            print('  ', baris_keluar)
        if h.returncode:
            galat.append(f'{" ".join(perintah)} GAGAL')

    print()
    if galat:
        print(f'❌ {len(galat)} masalah — JANGAN commit dulu:')
        for g in galat:
            print('   •', g)
        sys.exit(1)
    print('✅ semua pemeriksaan lolos.')
    print('   Langkah terakhir yang tidak bisa digantikan mesin: buka index.html di browser,')
    print('   lihat angkanya masuk akal atau tidak.')


if __name__ == '__main__':
    main()
