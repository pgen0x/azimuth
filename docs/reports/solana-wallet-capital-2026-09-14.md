# Mengapa PnL +$40,73 tetapi modal Azimuth berkurang

Snapshot 14 September 2026, sekitar 15:41 WIB. Audit ini membaca API dan transaksi publik; tidak menandatangani transaksi, menjual token, menutup akun, atau mengubah strategi live.

## Kesimpulan

+$40,73 adalah **PnL posisi LP Azimuth**, setara +0,340368699 SOL. Angka ini bukan perubahan kekayaan wallet. Setelah menyertakan arus pembelian dan penjualan token di luar LP, hasil closed LP + swap menjadi **−1,232878245 SOL**, sebelum gas dan valuasi sisa token. Penjelasan sebelumnya yang menekankan ukuran ticket/modal tidak cukup dan perlu dikoreksi.

Selisih dominan adalah **valuasi token pada batas LP versus hasil konversinya ke/dari SOL**, bukan gas. Selisih ini belum dipisah menjadi fee swap, price impact, pergerakan harga selama token berada di luar LP, dan perbedaan penilaian API. Menyebut semuanya “slippage” atau “IL” tidak dapat dibenarkan.

## Modal yang masih terlihat

| Komponen Azimuth | SOL |
|---|---:|
| Saldo SOL bebas | 0,261549729 |
| Nilai dua LP aktif + fee belum diklaim | 0,200319488 |
| Sisa token di wallet, estimasi harga pasar | 0,030838720 |
| Lamport di 79 akun token | 0,119244209 |
| Lamport di dua akun posisi LP | 0,083799680 |
| **Total aset teridentifikasi** | **0,695751826** |

Saldo SOL + nilai LP sekitar 0,462 SOL menjelaskan tampilan modal sekitar 0,5 SOL. Jika dibandingkan patokan 1,5 SOL yang disebut pengguna, aset teridentifikasi masih berkurang sekitar **0,80425 SOL**, bukan seluruhnya sekadar terkunci.

Sisa token bernilai sekitar $3,13 menurut Dexscreener. Empat mint tidak memiliki harga yang terverifikasi dan tidak dimasukkan, bukan dianggap pasti bernilai nol. Harga pasar bukan jaminan hasil jual. Total akun token mencakup 17 akun dengan saldo token nol, senilai **0,025506680 SOL**. Semua saldo akun tidak otomatis merupakan uang siap dipakai: penutupan bergantung pada otoritas dan kondisi akun; akun posisi aktif harus diperlakukan bersama posisi tersebut.

## Bukti selisih LP dan swap

Dari 267 pool dengan riwayat posisi tertutup:

| Rekonsiliasi | SOL |
|---|---:|
| Net SOL asli masuk/keluar closed LP | −73,484292623 |
| Net nilai token non-SOL menurut API pada deposit/withdraw/claim LP | +73,824661322 |
| **PnL closed LP yang ditampilkan API** | **+0,340368699** |
| SOL net dari konversi token non-SOL di luar LP | +72,251414378 |
| **Closed LP + konversi aktual** | **−1,232878245** |
| Selisih penilaian token LP dengan konversi aktual | **−1,573246944** |

Arus konversi mencakup 180 pembelian memakai 17,835 SOL dan 754 penjualan menghasilkan 90,086414378 SOL. Ini angka perputaran kumulatif, bukan modal awal. Pembelian sebelum deposit dan penjualan setelah withdrawal sama-sama masuk perhitungan. Perantara seperti USDC dalam satu route dinetkan, agar satu swap tidak salah dianggap beberapa transaksi independen.

Ada lima penerimaan SOL dari program lain, total **0,173772194 SOL**, tanpa pengurangan token lain dalam transaksi yang sama. Penerimaan ini dipisahkan dari swap dan profit LP. Tidak diasumsikan sebagai profit strategi atau setoran modal tanpa atribusi lebih lanjut.

Contoh agregat token, semua sebelum gas dan sebelum valuasi sisa token:

| Token | PnL LP API | LP + swap aktual |
|---|---:|---:|
| CatGPT | +0,004788 | **−0,097772** |
| fomocat | +0,020652 | **−0,060273** |
| MADE, dua pool | +0,034377 | **−0,045079** |
| BUTTHOLE, dua pool | +0,025222 | **−0,038000** |
| CTO, mint BmH3… | +0,032048 | **−0,027571** |

Ini agregat riwayat token, bukan klaim bahwa satu close tertentu menghasilkan seluruh kerugian tersebut. Detail semua 226 mint ada di `token-execution-gap.csv`.

## Biaya, setoran, dan saldo akhir

Total biaya jaringan yang benar-benar dibayar Azimuth adalah **0,079953127 SOL**. Termasuk transaksi gagal; fee yang dibayar wallet lain tidak dibebankan ke Azimuth.

Riwayat pendanaan wallet yang terlihat berbeda dari baseline nominal 1,5 SOL: masuk 0,0246 SOL pada 27 April, keluar 0,012 SOL pada 5 Mei, lalu masuk 1,8249754 SOL pada 28 Juli. Saldo sebelum operasi LP pertama pada 28 Juli sekitar **1,8374954 SOL**, setelah fee transaksi Mei. Jadi ROI tepat dari baseline 1,5 SOL memerlukan tanggal baseline tersebut; audit ini tidak mengganti ingatan pengguna dengan asumsi tanggal mulai.

Bridge sepanjang riwayat wallet:

| Arus | SOL |
|---|---:|
| Dua setoran native dikurangi transfer keluar Mei | +1,837575400 |
| Arus net WSOL melalui LP, swap, dan penerimaan program | −1,259105019 |
| Biaya jaringan wallet | −0,079953127 |
| Arus native lain net, termasuk dana akun | −0,236967525 |
| **Saldo native akhir, cocok on-chain** | **0,261549729** |

Dari kategori arus native lain, 0,203043889 SOL masih terlihat di akun token/posisi saat snapshot. **Sisa 0,033923636 SOL belum diatribusikan per jenis biaya/penerima**; tidak boleh diberi label pasti “rent hangus”. Tidak ditemukan pembayaran inisialisasi bin-array positif dari pemanggilan yang berhasil didekode; banyak transaksi berlabel INITIALIZE_BIN_ARRAY hanya memanggil initializer pada akun yang sudah ada. Label tipe transaksi provider sendiri tidak membuktikan adanya biaya baru.

Saldo wallet direkonsiliasi dari perubahan saldo transaksi, bukan dengan menjumlahkan `nativeTransfers` provider: array transfer tersebut tidak merepresentasikan semua refund akun dan tidak cocok untuk ledger lengkap.

## Perbandingan Meridian

Pada snapshot yang hampir bersamaan:

| Komponen | Azimuth | Meridian |
|---|---:|---:|
| SOL bebas | 0,26155 | 0,96537 |
| LP aktif + fee | 0,20032 | 0,49961 |
| Total aset teridentifikasi, termasuk akun dan token | **0,69575** | **1,74936** |
| PnL closed LP sepanjang riwayat API | +0,34037 / $40,73 | +0,88918 / $91,53 |

Riwayat keduanya tidak dimulai pada tanggal yang sama: LP pertama yang ditemukan Meridian 15 Juni; Azimuth 28 Juli. Meridian juga menerima transfer 2,33505854 SOL pada 19 Juni dari alamat sumber yang sama dengan pendanaan Azimuth. Itu tidak membuktikan modal strategi awal berbeda pada tanggal pembandingan yang dimaksud pengguna, tetapi membuat perbandingan saldo/lifetime PnL tanpa baseline setoran tidak valid.

Meridian juga mempunyai selisih konversi. Sejak LP pertama, arus native SOL closed LP −93,145924434 ditambah net konversi +91,983608788 menghasilkan **−1,162315646 SOL**, sebelum gas dan penilaian inventory. Angka ini merupakan arus LP + konversi dalam periode tersebut, bukan ROI wallet Meridian: inventory awal serta aktivitas wallet sebelumnya harus dinetkan untuk memperoleh ROI. Karena itu, profit LP Meridian juga tidak cukup untuk menyatakan strategi selalu menghasilkan profit bersih.

## Implikasi perbaikan

1. Ukuran keberhasilan harus perubahan NAV dalam SOL setelah setoran/penarikan dinetkan, dengan arus LP, swap, biaya, dan saldo akun terpisah. PnL LP tetap berguna, tetapi tidak boleh diberi arti “uang bersih kembali”.
2. Evaluasi hasil dari pembelian sebelum LP sampai penjualan setelah LP. Token hasil withdrawal yang belum dijual harus muncul sebagai inventory, bersama umur dan nilainya.
3. Evaluasi keputusan turnover/recenter terhadap hasil net setelah konversi. Hanya mengoptimalkan fee LP atau persentase posisi menang dapat mempertahankan pola yang tampak hijau tetapi mengurangi SOL.
4. Guard exit dan pencegahan entry ganda yang baru diterapkan tetap relevan, tetapi belum membuktikan masalah konversi/accounting ini selesai. Jangan menaikkan modal berdasarkan angka dashboard ini.

Tidak ada perubahan produksi tambahan dalam audit ini. Rekonsiliasi dan diagnosis didahulukan agar perbaikan berikutnya menargetkan sumber kehilangan yang terbukti.

## Validasi dan batas

- Azimuth: 7.448 signature unik. 7.390 tersedia melalui enhanced API; 58 yang tidak diindeks adalah transaksi gagal dan dibaca melalui RPC mentah. Seluruh perubahan saldo menjumlah tepat menjadi saldo snapshot, sampai satu lamport.
- Arus native SOL LP on-chain cocok dengan nilai native API closed LP ditambah deposit dua posisi terbuka, selisih di bawah 0,00000001 SOL. Ini memeriksa kelengkapan sisi SOL API secara independen.
- Meridian: 12.533 signature unik; enhanced pagination mengandung empat duplikat yang dibuang. Tiga transaksi gagal Januari 2025 tidak tersedia melalui endpoint archival yang dicoba; semuanya mendahului periode LP Juni 2026. Tidak diklaim bahwa ledger lifetime Meridian sudah lengkap.
- Snapshot wallet dan API tidak atomik dalam satu slot. Bot tetap berjalan. NAV memakai harga LP/token saat pengambilan, bukan nilai likuidasi yang dijamin.
- Selisih konversi adalah agregat observed-versus-marked; analisis ini tidak memisahkan fee DEX, price impact, delay, dan error harga API per trade.
- Jalankan `rtk proxy python3 /home/ubuntu/azimuth-audits/wallet-capital-2026-09-14/verify.py` untuk mengulang pemeriksaan atas snapshot tersimpan.

Sumber primer data: RPC Solana dan Helius enhanced transaction API untuk kedua alamat publik; [Meteora portfolio Azimuth](https://dlmm.datapi.meteora.ag/portfolio?user=3w2SBc58L3VSnoMGnvLcsGxXXJKVigmFagrB7ChRGa13&page=1&pageSize=50), [open portfolio Azimuth](https://dlmm.datapi.meteora.ag/portfolio/open?user=3w2SBc58L3VSnoMGnvLcsGxXXJKVigmFagrB7ChRGa13), seluruh halaman tersimpan lokal. [Dokumentasi akun Solana](https://solana.com/docs/core/accounts) menjelaskan saldo lamport pada akun; [dokumentasi biaya Solana](https://solana.com/docs/core/fees) menjelaskan biaya transaksi. Referensi harga sisa token: respons Dexscreener yang disimpan bersama audit.
