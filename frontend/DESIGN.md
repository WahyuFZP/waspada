# WASPADA: Design System

Dashboard pemantauan isu strategis untuk analis SOC. Dipandang lama dan dari jarak pandang, jadi tampilan gelap, tenang, dan warna hanya membawa makna.

Dial: ENERGY 2 / RHYTHM 2 / MOTION 2

## Struktur (branch `frontend-template`)

Mengikuti pola template "Cybersecurity Services" (aura.build): nav sticky, hero besar dengan judul dua warna, lalu panel dashboard berbingkai jendela. Bedanya, panel di WASPADA adalah dashboard live yang asli, bukan mockup, dan tidak ada statistik karangan.

Pengecualian antislop yang disetujui pemilik (21 Okt 2026):
- Glow radial di belakang judul hero: dipertahankan, satu saja, warna hijau TNI-AD (bukan merah template, supaya merah tetap khusus alert kritis).
- Radar beranimasi di hero: dipertahankan; hanya berputar saat stream SSE terhubung, jadi gerakannya menandai status nyata. Mati saat *reduce motion*.
- Bingkai jendela tiga titik di atas panel pemantauan: dipertahankan sebagai identitas visual template.
- Label kecil huruf kapital berjarak renggang: dipertahankan untuk label statistik dan status panel.

## Warna (token di `app/globals.css`)

Diambil dari identitas TNI Angkatan Darat: hijau loreng sebagai dasar, emas lambang Kartika Eka Paksi sebagai satu-satunya aksen.

| Token | Nilai | Dipakai untuk |
|---|---|---|
| `bg` | `#0B0D08` | Latar halaman, hijau-hitam, bukan hitam pekat |
| `surface` | `#13170E` | Panel dan kartu |
| `surface-2` | `#1C2215` | Kartu terpilih, hover |
| `line` | `#2A3120` | Garis pemisah |
| `army` | `#4B5320` | Hijau TNI-AD: state aktif (filter terpilih) |
| `ink` | `#ECEAE0` | Teks utama |
| `ink-muted` | `#A6AC92` | Teks sekunder (kontras 7:1 di atas `bg`) |
| `gold` | `#D4A72C` | Aksen: baris kedua judul hero, tombol utama, focus ring, titik media luar negeri di timeline |

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

Gerak hanya menandai kejadian, tidak berjalan terus-menerus. Semua dimatikan bila pengguna memilih *reduce motion*.

| Kejadian | Gerak |
|---|---|
| Alert baru | Masuk dari atas, kartu lain bergeser (layout spring) |
| Alert kritis baru | Cincin merah berdenyut 2x, toast muncul 8 detik |
| Buka detail | Panel naik + timeline muncul berurutan |
| Ganti filter | Indikator pilihan bergeser ke tombol aktif |

## Tata letak

- < 768px: satu kolom, detail tampil sebagai sheet dari bawah.
- 768–1279px: kartu alert dua kolom, arus berita di bawah.
- ≥ 1280px: alert (kiri) dan arus berita (kanan, 380px) berdampingan.
- Target sentuh minimal 44px.
