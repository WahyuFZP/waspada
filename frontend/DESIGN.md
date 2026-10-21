# WASPADA — Design System

Dashboard pemantauan isu strategis untuk analis SOC. Dipandang lama dan dari jarak pandang, jadi tampilan gelap, tenang, dan warna hanya membawa makna.

## Warna (token di `app/globals.css`)

Diambil dari identitas TNI Angkatan Darat: hijau loreng sebagai dasar, emas lambang Kartika Eka Paksi sebagai satu-satunya aksen.

| Token | Nilai | Dipakai untuk |
|---|---|---|
| `bg` | `#12150E` | Latar halaman, hijau-hitam, bukan hitam pekat |
| `surface` | `#1A1F14` | Panel dan kartu |
| `surface-2` | `#232A1A` | Kartu terpilih, hover |
| `line` | `#343C27` | Garis pemisah |
| `army` | `#4B5320` | Hijau TNI-AD: state aktif (filter terpilih) |
| `ink` | `#ECEAE0` | Teks utama |
| `ink-muted` | `#A6AC92` | Teks sekunder (kontras 7:1 di atas `bg`) |
| `gold` | `#D4A72C` | Aksen: focus ring dan titik media luar negeri di timeline (putih = dalam negeri) |

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
