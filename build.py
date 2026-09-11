#!/usr/bin/env python3
"""build.py — satukan data/*.json ke dalam index.html.

index.html sengaja TETAP memuat datanya di dalam berkas (bukan `fetch`) supaya dashboard
masih bisa dibuka dengan klik-ganda dari komputer — `fetch` dari `file://` diblokir browser.
Jadi: `data/*.json` = sumber kebenaran, blok di `index.html` = hasil generate.

    python3 build.py           tulis ulang blok data di index.html
    python3 build.py --check   GAGAL (exit 1) kalau index.html tidak sinkron dengan data/
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HTML = ROOT / 'index.html'
AWAL = '        // <<<DATA>>>'
AKHIR = '        // <<</DATA>>>'
AWAL_SUMBER = '        <!-- <<<SUMBER>>> -->'
AKHIR_SUMBER = '        <!-- <<</SUMBER>>> -->'
SUMBER = [('datasetTerritory', 'data/market.json'),
          ('datasetHamaPenyakit', 'data/hama_penyakit.json')]
JEJAK = ROOT / 'data' / '_sumber.json'
BULAN = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
         'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']


def blok() -> str:
    """Blok <script> yang digenerate — persis ini yang ditanam di antara dua penanda."""
    bagian = [AWAL,
              '        // ⚠️ DIGENERATE build.py DARI data/*.json — JANGAN EDIT DI SINI.',
              '        //    Ubah datanya di data/, lalu jalankan: python3 build.py']
    for nama, berkas in SUMBER:
        isi = (ROOT / berkas).read_text(encoding='utf-8').rstrip()
        bagian.append('')
        bagian.append(f'        const {nama} = {isi};')
    bagian.append(AKHIR)
    return '\n'.join(bagian)


def tanggal_indo(iso: str) -> str:
    """'2026-09-09' → '9 September 2026'. Kalau bentuknya lain, kembalikan apa adanya."""
    bagian = iso.split('-')
    if len(bagian) != 3 or not all(x.isdigit() for x in bagian):
        return iso
    th, bl, tg = bagian
    return f'{int(tg)} {BULAN[int(bl) - 1]} {th}'


def blok_sumber() -> str:
    """Kaki halaman: kapan datanya, dari mana, dan peringatan bahwa ini estimasi.

    Dashboard ini sering di-forward sebagai tautan/tangkapan layar. Tanpa baris ini,
    penerimanya tidak punya cara tahu angkanya per kapan.
    """
    if not JEJAK.exists():
        return '\n'.join([AWAL_SUMBER, AKHIR_SUMBER])
    d = json.loads(JEJAK.read_text(encoding='utf-8'))
    tebal = 'class="text-slate-300 font-semibold"'
    baris = [f'        <div>Data per <span {tebal}>{tanggal_indo(d.get("tanggal_data", "-"))}</span>'
             f' · versi {d.get("versi", "-")} · {d.get("cakupan", "")}</div>']
    if d.get('sifat') == 'estimasi':
        baris.append('        <div class="text-amber-500/80 mt-0.5">⚠ Angka di halaman ini '
                     '<span class="font-semibold">estimasi</span>, bukan hasil pengukuran resmi.</div>')
    if d.get('catatan'):
        baris.append(f'        <div class="mt-0.5">{d["catatan"]}</div>')
    if d.get('sumber'):
        baris.append(f'        <div class="mt-0.5 text-slate-600">Sumber: {d["sumber"]}</div>')
    return '\n'.join([AWAL_SUMBER] + baris + [AKHIR_SUMBER])


def _ganti(teks: str, awal: str, akhir: str, isi: str) -> str:
    i, j = teks.find(awal), teks.find(akhir)
    if i < 0 or j < 0:
        sys.exit(f'❌ penanda {awal.strip()} / {akhir.strip()} tak ketemu di index.html')
    return teks[:i] + isi + teks[j + len(akhir):]


def susun() -> str:
    teks = HTML.read_text(encoding='utf-8')
    teks = _ganti(teks, AWAL, AKHIR, blok())
    return _ganti(teks, AWAL_SUMBER, AKHIR_SUMBER, blok_sumber())


def main() -> None:
    baru = susun()
    if '--check' in sys.argv:
        if baru != HTML.read_text(encoding='utf-8'):
            sys.exit('❌ index.html BASI — isinya beda dari data/*.json.\n'
                     '   Jalankan: python3 build.py')
        print('✅ index.html sinkron dengan data/')
        return
    HTML.write_text(baru, encoding='utf-8')
    print(f'✅ index.html diperbarui dari {len(SUMBER)} berkas di data/')


if __name__ == '__main__':
    main()
