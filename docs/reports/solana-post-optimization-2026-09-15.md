# Hasil setelah optimasi Solana — 15 September 2026

Snapshot pembandingan berakhir **15 September 09:08 WIB**. Patch exit/entry 0b77a72 mulai live **14 September 15:23:49 WIB**, sehingga baru 17 jam 44 menit berlalu, belum 24 jam penuh.

**Belum terbukti meningkat. Penyebab utama jumlah posisi tertinggal adalah gangguan autentikasi Redis, yang sekarang sudah diperbaiki.**

## Angka pengguna terkonfirmasi

Periode 24 jam: 14 September 09:08 sampai 15 September 09:08 WIB.

| Metrik | Azimuth | Meridian |
|---|---:|---:|
| Posisi tertutup | 12 | 37 |
| WR berdasarkan PnL USD | 58,33% (7/12) | 62,16% (23/37) |
| WR berdasarkan PnL SOL | 66,67% | 70,27% |
| PnL LP SOL | +0,000176466 | +0,016044821 |
| PnL LP USD | +$0,30436 | +$3,08910 |
| Posisi masih terbuka pada snapshot | 0 | 2 |

Jadi “12 vs 37” adalah jumlah **close** dalam periode, bukan jumlah posisi yang masih open bersamaan. WR USD berbeda dari WR SOL karena denominasi. Semua PnL tabel adalah PnL LP dan belum merupakan profit bersih wallet setelah swap.

## Periode yang benar-benar sesudah patch

| Metrik, 14 Sep 15:23:49 — 15 Sep 09:08 | Azimuth | Meridian |
|---|---:|---:|
| Posisi ditutup | 5 | 29 |
| WR USD | 40,00% | 58,62% |
| PnL LP SOL | −0,002840139 | +0,004829418 |
| Posisi baru dalam periode, sudah ditutup | 3 | 28 |
| Posisi baru dalam periode, masih terbuka | 0 | 2 |
| PnL LP dari posisi baru yang sudah tutup | −0,000531224 | +0,022592393 |

Dua close Azimuth adalah posisi yang sudah terbuka sebelum patch, sehingga seluruh hasilnya tidak boleh diatribusikan kepada patch baru. Sampel baru Azimuth hanya tiga close.

Sebagai pembanding deskriptif, 17 jam 44 menit sebelum patch Azimuth menutup 36 posisi dengan PnL LP +0,004103364 SOL. Ini bukan uji kausal strategi: kondisi pasar dan tingkat ketersediaan sistem berbeda.

## Bottleneck yang ditemukan

Redis server mulai berjalan dengan autentikasi pada **14 September 19:45:01 WIB**. Error pertama monitor tercatat 19:45:17; scanner 19:45:49. Kedua aplikasi masih hidup, tetapi tidak membawa password Redis.

- Scanner: **9.450** pesan `NOAUTH Authentication required`; **1.606** siklus gabungan turnover/pulse selama gangguan, **nol kandidat terkirim**.
- Monitor: **2.296** baris NOAUTH. Pesan error Redis bahkan dibaca sebagai nama posisi `NOAUTH Authentication required.`; scoreboard juga gagal mengubah pesan tersebut menjadi float.
- Durasi gangguan dalam window audit: **13 jam 23 menit**, sekitar 75% periode sesudah patch.
- Sebelum error Redis, kedua bot sama-sama menutup **5 posisi** sejak patch. Setelah error, Azimuth menutup **0**, sementara Meridian menutup **24** lagi.
- Posisi Azimuth terakhir tutup 14 September 19:28:57 WIB; swap terakhir 19:31:56, sebelum Redis bermasalah. Tidak ada posisi nyata terbuka pada snapshot audit.

Ini menunjukkan bottleneck operasional yang kuat. Tidak ada dasar melonggarkan filter risiko hanya untuk mengejar jumlah transaksi Meridian.

## Apakah perbaikan strategi bekerja?

Ada bukti guard exit berjalan: NINA yang sudah terbuka sebelum patch keluar lewat fast-out pada tanda PnL +5,17%, dengan hasil LP +0,005115112 SOL. Namun EMBERCAT, posisi lama yang diadopsi sebagai spot, tetap berakhir −0,007424027 SOL lewat hard stop.

Masalah konversi juga masih terlihat. Noiz:

- Deposit: 0,159999977 SOL.
- SOL yang ditarik + fee SOL: 0,094468242 SOL.
- Token Noiz hasil withdrawal + fee: 5.895,311313, seluruhnya muncul pada transaksi swap berikutnya.
- Hasil swap: 0,063230767 SOL, sekitar 179 detik setelah close.
- **Hasil aktual sebelum gas: −0,002300968 SOL**; API LP menampilkan −0,000530079 SOL.

Dengan demikian, terdapat tambahan selisih konversi sekitar 0,001770889 SOL. Tidak disimpulkan semuanya fee atau slippage; perubahan harga antara close dan swap dan valuasi API belum dipisahkan. NINA lama dan inventory EMBERCAT dari sebelum window juga membuat perubahan saldo wallet saja tidak cukup untuk mengukur profit window. Audit ini tidak mengklaim NAV sesudah patch sudah meningkat.

## Perbaikan yang sudah diterapkan

Branch **codex/solana-redis-auth**, worktree `/home/ubuntu/azimuth-redis-auth`, commit **d0c3e272cc4c42d443f8ebdead5e4706821368a0** sudah dipush.

Go store sekarang membaca `REDISCLI_AUTH`, variabel yang juga dipakai `redis-cli`. Credential Redis yang sudah berlaku dipasang pada environment daemon dan profil Solanza; konfigurasi autentikasi server tetap berlaku. Credential tidak masuk git atau laporan. Monitor memuat ulang environment setiap tick. Gateway Hermes memiliki pemuatan ulang environment per turn, sehingga tidak perlu restart gateway untuk mengubah credential.

Binary dibangun dari worktree bersih, lalu diterapkan **15 September 09:13:57 WIB**. Perubahan kecil source juga diterapkan pada checkout utama tanpa menimpa perubahan pengguna yang sudah ada; commit branch utama tidak dipindahkan. Hash semua perubahan pengguna sebelum tindakan cocok setelah patch autentikasi dikecualikan.

Validasi:

- `go vet ./...`, `go test ./internal/...`, dan build lulus di worktree.
- Test integrasi read-only ke Redis live lulus: client dengan credential berhasil PING; client tanpa credential ditolak.
- Scanner dan monitor active/enabled, restart otomatis 0.
- Siklus berikutnya **09:14:57 WIB** berhasil membaca cooldown/momentum dan mengirim sinyal PVE. Ini bukti pemrosesan kandidat pulih, bukan klaim sudah membuka posisi baru.
- Monitor kembali membaca active set dengan benar. Tidak ada NOAUTH di log sesudah perbaikan yang disimpan.
- Robinhood tetap nonaktif. Parameter strategi dan sizing tidak diubah dalam perbaikan Redis ini.

Baseline pengamatan operasional baru mulai **15 September 09:13:57 WIB**. Tidak ada jadwal otomatis baru dibuat oleh audit ini.

## Sumber dan batas data

Data terbuka diambil langsung dari Meridian API, status HTTP 200 untuk kedua wallet. Riwayat close diambil dari seluruh halaman Meteora portfolio/pnl untuk pool yang relevan, 0 error, lalu dijoin dengan journal kedua bot. `positions.csv`, `summary.json`, raw API, journal, dan log disimpan di direktori ini.

On-chain swap Noiz diperiksa melalui enhanced transaction API. Upaya tambahan RPC untuk memeriksa seluruh signature window terkena HTTP 429; audit ini tidak menyatakan total gas atau ledger seluruh wallet window lengkap. Nilai Noiz dilaporkan sebelum gas. PnL LP berbeda dari PnL wallet sesuai audit kapital 14 September.
