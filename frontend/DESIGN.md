# WASPADA: Design System

Dashboard pemantauan isu strategis untuk analis SOC. Dipandang lama dan dari jarak pandang, jadi tampilan gelap, tenang, dan warna hanya membawa makna.

Dial: ENERGY 2 / RHYTHM 2 / MOTION 2

## Struktur (branch `frontend-template`)

Mengikuti pola template "Cybersecurity Services" (aura.build): nav sticky, hero besar dengan judul dua warna, lalu panel dashboard berbingkai jendela. Bedanya, panel di WASPADA adalah dashboard live yang asli, bukan mockup, dan tidak ada statistik karangan.

Pengecualian antislop yang disetujui pemilik (21 Okt 2026):
- Glow radial di belakang judul hero: dipertahankan, satu saja, hijau perisai Pussiberad (bukan merah template, supaya merah tetap khusus alert kritis).
- Animasi berulang di hero: radar diganti **jaring pertahanan** (lihat Gerak); paket hanya bergerak saat stream SSE terhubung, jadi gerakannya menandai status nyata. Mati saat *reduce motion*.
- Bingkai jendela tiga titik di atas panel pemantauan: dipertahankan sebagai identitas visual template.
- Label kecil huruf kapital berjarak renggang: dipertahankan untuk label statistik dan status panel.

## Warna (token di `app/globals.css`)

Diambil dari lambang Pussiberad (Pusat Siber TNI AD), diukur dari lambang pada poster HUT ke-6 Pussiberad: perisai hijau (`#488547`, sorotan `#60B45F`), bingkai/bintang/pita emas (`#D6AF58`), bola dunia merah-putih (`#CA373B` / putih). Merah dipertahankan sebagai warna severity kritis saja.

| Token | Nilai | Dipakai untuk |
|---|---|---|
| `bg` | `#070D08` | Latar halaman, hijau-hitam, bukan hitam pekat |
| `surface` | `#0D170F` | Panel dan kartu |
| `surface-2` | `#142217` | Kartu terpilih, hover |
| `line` | `#213426` | Garis pemisah, rel alur korelasi |
| `siber` | `#3F7A40` | Hijau perisai (digelapkan agar teks putih di atasnya kontras): state aktif, filter terpilih |
| `siber-bright` | `#60B45F` | Sorotan perisai: status terhubung, simpul jaring |
| `ink` | `#F1F4EF` | Teks utama |
| `ink-muted` | `#A7B8A6` | Teks sekunder |
| `gold` | `#D6AF58` | Aksen emas: baris kedua judul hero, tombol utama, focus ring, paket data, titik media luar negeri |

Severity selalu ditulis dengan label teks, bukan hanya warna:

| Severity | Label | Token |
|---|---|---|
| critical | KRITIS | `sev-critical` `#F05252` |
| high | TINGGI | `sev-high` `#F2913D` |
| medium | SEDANG | `sev-medium` `#EADB5B` |
| low | RENDAH | `sev-low` `#9AA08A` |

## Tipografi: tiga font, tiga peran

| Peran | Font | Kelas | Alasan |
|---|---|---|---|
| Headline | Barlow Condensed (600/700) | `font-display` | Huruf rapat bergaya papan penanda; tegas dan hemat ruang di layar lebar |
| Deskripsi | Public Sans (400/500) | `font-body` (default `body`) | Sans netral dari sistem desain pemerintahan; resmi dan mudah dibaca untuk judul berita |
| Pesan kecil | IBM Plex Mono (400/500) | `font-data` | Label, waktu, sumber, badge; angka sejajar sehingga timestamp terbaca rapi |

Aturan: tidak ada font keempat. Teks yang bukan headline dan bukan deskripsi memakai `font-data`.

## Nada bahasa

Tegas tetapi sopan. Kalimat pendek, kata kerja aktif, tanpa seruan dan tanpa emoji.
Contoh: "Sambungan ke server pemantauan terputus. Sistem akan menyambung ulang secara otomatis."

## Gerak

Gerak hanya menandai kejadian atau status nyata. Satu-satunya gerak berulang adalah paket di jaring hero, dan itu hanya berjalan saat stream terhubung. Semua dimatikan bila pengguna memilih *reduce motion*.

| Kejadian | Gerak |
|---|---|
| Alert baru | Masuk dari atas, kartu lain bergeser (layout spring) |
| Alert kritis baru | Cincin merah berdenyut 2x, toast muncul 8 detik |
| Buka detail | Panel naik + timeline muncul berurutan |
| Ganti filter | Indikator pilihan bergeser ke tombol aktif |
| Stream terhubung | **Jaring pertahanan** di hero (bola dunia berjaring, motif lambang Pussiberad): paket emas bergerak dari simpul ke inti korelasi. Saat terputus, paket berhenti dan simpul meredup |
| Alert baru dari stream | Inti jaring memancarkan satu gelombang merah |
| Event / alert baru dari stream | **Alur korelasi** (Ingest → Normalisasi → Korelasi → Peringatan): paket emas per event menuju Korelasi, paket merah per alert menuju Peringatan. Tanpa data baru, alur diam |
| Panel pemantauan masuk layar | Naik halus sekali (scroll reveal) |

## Tata letak

- < 768px: satu kolom, detail tampil sebagai sheet dari bawah.
- 768–1279px: kartu alert dua kolom, arus berita di bawah.
- ≥ 1280px: alert (kiri) dan arus berita (kanan, 380px) berdampingan.
- Target sentuh minimal 44px.
