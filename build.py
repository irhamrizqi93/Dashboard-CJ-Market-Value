#!/usr/bin/env python3
"""build.py — satukan data/*.json ke dalam index.html.

index.html sengaja TETAP memuat datanya di dalam berkas (bukan `fetch`) supaya dashboard
masih bisa dibuka dengan klik-ganda dari komputer — `fetch` dari `file://` diblokir browser.
Jadi: `data/*.json` = sumber kebenaran, blok di `index.html` = hasil generate.

    python3 build.py           tulis ulang blok data di index.html
    python3 build.py --check   GAGAL (exit 1) kalau index.html tidak sinkron dengan data/
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HTML = ROOT / 'index.html'
AWAL = '        // <<<DATA>>>'
AKHIR = '        // <<</DATA>>>'
SUMBER = [('datasetTerritory', 'data/market.json'),
          ('datasetHamaPenyakit', 'data/hama_penyakit.json')]


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


def susun() -> str:
    teks = HTML.read_text(encoding='utf-8')
    i, j = teks.find(AWAL), teks.find(AKHIR)
    if i < 0 or j < 0:
        sys.exit('❌ penanda <<<DATA>>> / <<</DATA>>> tak ketemu di index.html')
    return teks[:i] + blok() + teks[j + len(AKHIR):]


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
