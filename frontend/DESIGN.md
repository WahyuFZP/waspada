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

## Tipografi: empat font, empat peran

| Peran | Font | Kelas | Alasan |
|---|---|---|---|
| Judul pendek (H1/H2 sampai 3 kata) | Silkscreen (400/700) | `font-pixel` | Wajah tema piksel 8-bit: nama merek, judul bagian, tombol, nomor tahap. Huruf lebar mirip kapital, jadi hanya untuk kata pendek |
| Judul panjang dan teks informasi | Pixelify Sans (400/500/700) | `font-body` (default `body`) | Tetap bergaya piksel, tetapi huruf besar-kecilnya jelas, jadi kalimat panjang dan headline 4+ kata cepat dibaca juri |
| Label data | IBM Plex Mono (400/500) | `font-data` | Waktu, IP, port, kode MITRE, badge; angka sejajar dan karakter mirip (0/O, 1/l) mudah dibedakan |
| Judul kartu dan angka statistik | Barlow Condensed (600/700) | `font-display` | Masih dipakai di kartu alert, nama tahap alur, dan angka statistik |

Aturan:
- Tidak ada font kelima.
- H1/H2 pendek memakai `font-pixel`. H1/H2 berupa kalimat atau 4+ kata (hero, "Periksa APK sebelum dipasang", nama rule di detail alert, status analisa akhir) memakai `font-body` tebal.
- Teks `font-body` minimal 16px (`text-base`): font piksel kehilangan bentuk huruf di bawah ukuran itu. Jarak baris body 1,6.
- Data yang harus dibedakan per karakter (IP, waktu, hash, nama file) tetap `font-data`.

### Gaya piksel ringan (di luar landing)

Landing memakai tema piksel penuh. Halaman kerja (pemantauan, log, APK) memakai bingkainya: logo kentongan berpiksel (`LogoMark`, tajam di 34px), nama merek `font-pixel`, judul H1/H2 piksel sesuai aturan di atas, tombol blok bersudut tajam dengan bayangan offset yang kempis saat ditekan, nomor tahap persegi, titik status persegi, dan latar kisi piksel di hero. Panel data tetap tenang supaya mudah dibaca.

## Nada bahasa

Tegas tetapi sopan. Kalimat pendek, kata kerja aktif, tanpa seruan dan tanpa emoji.
Contoh: "Sambungan ke server pemantauan terputus. Sistem akan menyambung ulang secara otomatis."

## Gerak

Gerak hanya menandai kejadian atau status nyata. Satu-satunya gerak berulang adalah paket di jaring hero, dan itu hanya berjalan saat stream terhubung. Semua dimatikan bila pengguna memilih *reduce motion*.

Pengecualian yang disetujui pemilik (3 Nov 2026): **latar sinyal** (`components/signal-lines.tsx`) di landing, dashboard, Log keamanan, dan Pemeriksa APK. Garis pendek melintas acak di jalur horizontal/vertikal kelipatan 5%, menggambarkan sinyal dari banyak sumber yang diolah WASPADA (*Wide-Area Signal Processing*). Hijau = sinyal, emas = paket data. Opasitas 0,45 di belakang semua panel agar teks tetap terbaca; tidak dirender saat *reduce motion*.

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
| Section lain masuk layar (alur korelasi, kotak unggah, riwayat, detail hasil scan) | Naik halus sekali, komponen `Reveal` |
| Landing dibuka | Kentongan berpiksel berayun sekali dari gantungannya, per bingkai (`steps`), lalu diam, seperti baru dipukul: peringatan dibunyikan. Mati saat reduce motion dan di layar < 768px |
| Landing digulir | Kentongan berayun mulus ke kanan-kiri dari gantungannya mengikuti kecepatan gulir, seperti gantungan kunci: bergoyang beberapa kali lalu diam, tanpa gerak naik-turun. Satu-satunya gerak halus di landing, atas permintaan pemilik; mati saat reduce motion dan di layar < 768px |
| APK sedang diunggah/dianalisis | Garis pindai bergerak di layar ponsel 3D dan titik di kartu berkedip; diam saat tidak ada proses |
| Halaman Pemeriksa APK terbuka | Lima kartu pemeriksaan (izin, sertifikat, URL dan domain, kode tersembunyi, judi online) terus keluar-masuk dari layar ponsel bergantian. Isinya apa yang diperiksa, bukan hasil: halaman unggah belum punya hasil scan |
| Baris log baru di `/log` | Meluncur masuk dari atas dengan sorotan emas yang memudar 2,2 detik; baris lain bergeser (layout) |
| Grafik log per menit | Tinggi batang menyesuaikan dengan spring saat log masuk; tooltip rincian saat hover |
| Pengirim log aktif (log dalam 5 menit) | Titik hijau berdenyut di "Sumber log"; diam dan abu-abu bila pengirim berhenti |
| Hasil scan dibuka | Skor naik dari 0 ke nilainya (akumulasi bobot aturan). Dimulai di frame pertama agar angka asli tetap tampil bila browser belum menggambar |

## Motif 3D: perangkat fisik

Objek tanpa WebGL di `components/objects-3d.tsx`, hanya yang punya makna. **Ponsel berisi paket APK** di Pemeriksa APK: wajah SVG ditumpuk beberapa lapis sepanjang sumbu Z lalu dimiringkan dengan perspektif CSS. **Kentongan** (logo, peringatan dini) di landing digambar sebagai piksel 16×16 (`crispEdges`) dengan bayangan offset 1 piksel, senada dengan tema piksel landing. Ini satu-satunya unsur berwarna non-severity di landing: logo tetap memakai warna identitas (hijau perisai, emas). Dashboard tidak memakai objek 3D agar tetap tenang untuk analis.

Unit nyata diberi kelas `.slab` (bayangan keras bertumpuk tanpa blur, `app/globals.css`) agar tampak seperti perangkat fisik: kartu modul di landing (ditambah `.slab-press`, tertekan saat disorot), tahap alur korelasi, dan kotak unggah APK. Tidak dipakai untuk semua kartu.

## Tata letak

- < 768px: satu kolom, detail tampil sebagai sheet dari bawah.
- 768–1279px: kartu alert dua kolom, arus berita di bawah.
- ≥ 1280px: alert (kiri) dan arus berita (kanan, 380px) berdampingan.
- Target sentuh minimal 44px.
