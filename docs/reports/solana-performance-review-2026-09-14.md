# Evaluasi Solana Azimuth vs Meridian — 14 September 2026

**Kesimpulan:** 24 jam terakhir Azimuth sudah positif tipis, tetapi kumulatif sejak deployment masih negatif. Perbaikan bentuk entry dan retry momentum bekerja; konsistensi profit belum tercapai. Dua masalah eksekusi yang terkonfirmasi lebih layak diprioritaskan daripada melonggarkan screening: entry paralel pada pool yang sama, serta trailing stop yang dibatalkan indikator sehingga guard downtrend tidak mengambil alih.

Audit ini hanya membaca live data dan menulis artefak analisis; tidak mengubah strategi, melakukan transaksi, atau restart layanan. Source pembanding ada di `/home/ubuntu/meridian`. Checkout live berisi perubahan lokal Robinhood dari pekerjaan lain; tidak disentuh.

## Window dan rekonsiliasi

- Deployment: **12 September 2026 23:37:28 WIB**, commit `7536052`.
- 24h pertama: 12 September 23:37:28 sampai 13 September 23:37:28 WIB.
- Kumulatif: deployment sampai **14 September 13:02:00 WIB** = 37h 24m 32s.
- 24h terbaru: 13 September 13:02:00 sampai 14 September 13:02:00 WIB. Window ini overlap dengan 24h pertama; jangan menjumlahkan keduanya.
- Meridian API `/api/positions/open/raw` berhasil HTTP 200 untuk kedua wallet. Data closed dibaca langsung dari API Meteora yang digunakan Meridian: seluruh pagination portfolio (267 pool Azimuth, 482 Meridian), lalu detail closed untuk 32/37 pool yang aktif sejak awal window pembanding sebelum deployment. **Tidak ada request detail yang gagal.** API dan journal dibekukan dalam folder laporan ini.
- Kumulatif setelah deployment: 98 posisi API Azimuth, 65 Meridian, tanpa duplikasi position address. Seluruh identitas arus dana `withdrawal + fees - deposit = pnlSol` cocok dalam toleransi 1e-7 SOL. Journal Azimuth mempunyai 97 baris / 95 posisi unik: dua baris duplikat dan tiga close API tanpa journal (Noiz, PURPS, CHILLHOUSE; hold hanya 7–16 detik). Seluruh 65 posisi Meridian cocok ke performance journal.
- Dalam 24h pertama, Azimuth 71 close termasuk satu DOGE-1 yang sudah ada saat deployment (+0,000248600 SOL). Hanya entry setelah deployment: **70 close, −0,009928659 SOL**. Meridian juga mempunyai satu posisi sebelum cutover; 38 entry baru menghasilkan +0,094045050 SOL.
- Raw journal Azimuth kumulatif menyatakan −0,011374 SOL, atau −0,012290 SOL sesudah dedup. Angka tersebut adalah mark sebelum settlement dan tidak menggantikan hasil flow API −0,008352971 SOL.

**Definisi:** seluruh PnL berikut adalah hasil arus LP dalam SOL. Belum mencakup rekonsiliasi seluruh gas/priority fee, swap sebelum/sesudah LP, slippage dan rent yang tidak kembali; posisi terbuka juga terpisah. Return memakai total deposit yang berulang, bukan ROI modal wallet. `Principal change` adalah withdrawal dikurangi deposit, **bukan IL terhadap HODL**. Karena itu hasil ini tidak membuktikan laba bersih wallet atau IL murni.

## Hasil pada window yang sama

| Window | Close Azimuth / Meridian | LP PnL Azimuth | LP PnL Meridian | Return/deposit Azimuth / Meridian |
|---|---:|---:|---:|---:|
| 24h pertama | 71 / 39 | -0.009680 SOL | +0.098837 SOL | -0.108% / +0.507% |
| 24h terbaru | 62 / 43 | +0.004457 SOL | -0.013005 SOL | +0.061% / -0.060% |
| Sejak deployment | 98 / 65 | -0.008353 SOL | +0.068762 SOL | -0.068% / +0.212% |

| Metrik 24h pertama | Azimuth | Meridian |
|---|---:|---:|
| Deposit berulang SOL | 8.959959 | 19.499999 |
| Fee LP SOL | 0.043119 | 0.198421 |
| Perubahan principal SOL | -0.052799 | -0.099584 |
| Fee/deposit % | 0.481 | 1.018 |
| Principal change/deposit % | -0.589 | -0.511 |
| Win rate % | 52.11 | 74.36 |
| Profit factor | 0.68 | 15.35 |
| Median hold menit | 16.13 | 15.45 |

Dibanding 24h sebelum deployment, principal change/deposit Azimuth membaik dari **−1,448% ke −0,589%**, tetapi fee/deposit turun dari **1,422% ke 0,481%**. Return/deposit justru turun dari −0,025% ke −0,108%. Jadi perlindungan principal membaik dalam observasi ini, namun fee belum cukup menutup erosi principal. Perubahan pasar dan pilihan pool turut memengaruhi; ini bukan estimasi kausal patch.

Pada **11 pool bersama di 24h pertama**, Azimuth +0,001203 SOL / +0,0201% deposit; Meridian +0,048239 SOL / +0,3446%. Perbedaan bukan hanya karena pool eksklusif atau ukuran modal. Namun entry-time, rentang bin, dan fee share juga berbeda sehingga bukan pertandingan posisi identik.

24h terbaru Azimuth +0,004457 SOL (sekitar +$0,30 menurut flow USD API) dan Meridian −0,013005 SOL. Meridian mengalami satu loss **INDEX −0,098646 SOL**, sekitar −19,73% dari deposit 0,5 SOL walaupun alasan journal stop-loss mencatat −8,61%. Mark exit tidak sama dengan settlement. Pada tambahan 13h24m setelah 24h pertama, win rate Meridian 84,62% tetapi PnL −0,030075 SOL: win rate tinggi sendiri tidak menjamin profit.

## Apa yang sudah bekerja

1. **Entry SOL-only benar-benar diterapkan.** Semua 98 close Azimuth setelah cutover mempunyai nol token-X pada deposit API (pool SOL=Y). Tidak ada `balanced_tight` pada journal periode ini. Dua label `spot` adalah metadata posisi adopsi setelah timeout re-center; API menunjukkan deposit SOL-only dan 21 bin. Jangan menyimpulkan strategi spot baru diaktifkan dari label tersebut.
2. **Retry momentum bekerja.** Dalam 24h pertama ada 2.315 momentum reject dan 1.193 cycle unmark; dalam seluruh window 3.270 reject dan 1.701 cycle unmark. Contoh FRIES pool `953MwRPr`: reject 12 September 17:46:28 UTC lalu sinyal kembali dikirim sekitar 17:47:29 UTC. Kandidat tetap harus melewati gate lain; pengiriman bukan bukti entry/profit. Analisis eksploratif 86 pasangan reject→send menggunakan label ticker disimpan terpisah dan tidak dianggap 86 pool/profit unik.
3. **Layanan stabil dalam window.** Kedua service tetap PID deployment, restart count 0; SHA256 binary yang berjalan cocok baseline. Scanner mencatat 1.440 cycle per mode di 24h pertama, 2.245 per mode sampai cutoff. Tidak ada webhook delivery-error atau `hermes` missing-PATH pada log periode ini. Ini tidak membuktikan setiap hasil analisis LLM berhasil. Ada 358 batch webhook, 90 eksekusi jalur direct selesai (7 deployed=true), sehingga fallback deterministik juga aktif.
4. **Pulse tetap layak dipertahankan.** 17 close pulse +0,002459 SOL; 78 turnover −0,010803 SOL; tiga close tanpa atribusi mode −0,000009 SOL.

## Bottleneck dan pola loss yang terkonfirmasi

### 1. Entry paralel: scanner vs monitor, dan antarjalur entry

API membuktikan **10 pasangan interval posisi overlap di lima pool**: PERPSPAD, TWINE, EMBERCAT, MIZO, PURPS, termasuk overlap leg lanjutan dengan posisi paralel. Tidak semua overlap berasal dari sebab yang sama atau menghasilkan loss; jangan menjumlahkan PnL pasangan karena satu posisi dapat muncul lebih dari sekali.

Kasus paling jelas **PERPSPAD, 14 September 04:54 WIB**:

- Monitor menutup root `1ayH8EvR...`, lalu re-center `HhJnwg7W...` dibuat **04:54:34**.
- Scanner direct-deploy membuka `2G6rKc9s...` di **pool yang sama pada 04:54:35**, satu detik kemudian.
- Kedua posisi 0,1 SOL tumpang tindih sekitar 20m50s. Scanner memang mencatat `direct deploy done (deployed=true)` untuk posisi kedua; monitor mencatat re-center pertama.
- Leg re-center tersebut +0,005561 SOL; posisi scanner paralel berakhir **−0,010005 SOL**. Ini exposure tambahan yang nyata, bukan duplikasi baris journal.

Source pipeline memeriksa `open_pools` sebelum deploy, sedangkan monitor melakukan close→hapus tracking→swap→deploy langsung melalui executor. Tidak ada reservasi atomik bersama lintas jalur dalam flow tersebut. Pemeriksaan snapshot tidak cukup menahan dua submit yang berdekatan.

**Prioritas perbaikan:** reservasi pool/mint yang sama dipakai entry pipeline, re-center dan pemulihan timeout, ditahan sampai posisi baru terkonfirmasi/tercatat. Recheck exposure setelah mengambil reservasi. Jangan mengganti masalah concurrency dengan sekadar TTL sinyal lebih panjang.

### 2. Trailing stop bisa dibatalkan indikator; guard downtrend tertutup

Pada `2G6rKc9s...` PERPSPAD, peak tercatat **+2,79%** dan trailing floor **+2,19%**. Ada 114 penundaan exit untuk pair ini antara 14 September **05:00:34–05:54:26 WIB** (sebagian periode masih mempunyai dua posisi). Setelah leg lain ditutup, log secara eksplisit menunjukkan posisi ini pada −3,38%, −4,23%, dst tetap ditunda karena `supertrend_break` menolak exit. Akhirnya hard SL pada mark −9,23%; API settlement −0,010005 SOL, sekitar −10,00% dari deposit.

Urutan kode menjelaskan masalah:

1. Trailing mengisi `close_reason`.
2. Kedua guard downtrend (termasuk floor tanpa konfirmasi) menggunakan `if not close_reason`, sehingga dilewati.
3. Timing-check membolehkan indikator menunda trailing. Bypass downtrend tidak berlaku karena reason masih berlabel trailing.
4. Akibatnya posisi yang sudah melewati floor downtrend tetap hidup sampai hard SL.

**Prioritas perbaikan:** risk floor harus mengalahkan reason profit yang bisa ditunda, dan trailing stop yang sudah armed pada turnover/pulse perlu keputusan eksekusi yang tidak dibatalkan indikator arah harga. Uji replay kasus PERPSPAD pada +2,79%→−3,38%→−9,23%, termasuk coexistence trailing+downtrend. Mengubah angka trigger saja tidak menyelesaikan urutan guard ini.

Total penundaan indikator 447 baris: FROGE 242, PERPSPAD 114, UBI 47, TWINE 25, EMBERCAT 8, Noiz 7, NINA 4. Ini tick penundaan, bukan 447 trade gagal.

### 3. Re-center terlalu sering tanpa evaluasi entry baru yang setara

| Label leg Azimuth sejak deployment | Close | LP PnL SOL |
|---|---:|---:|
| sol_bidask | 49 | +0,000462 |
| turnover_rebalance | 44 | −0,008823 |
| spot/adopsi | 2 | +0,000017 |
| tanpa journal | 3 | −0,000009 |

Leg rebalance median **21 bin**, initial sol_bidask **45 bin**, Meridian **58 bin** menurut rentang API. Jumlah bin berbeda fee density dan exposure; bukan alasan otomatis memperlebar seluruh posisi. Re-center memakai deploy executor langsung dengan 20 bins-below, melewati screening/momentum/rent pipeline entry baru.

- **Tokabu:** root hampir impas (+0,000006), leg re-center −0,007086; total root-chain −0,007080 SOL.
- **ALL:** root +0,001482, leg berikut +0,003776 lalu −0,000011 lalu −0,011048 dalam ~6,5 menit; total root-chain −0,005801 SOL.
- **PERPSPAD:** root + dua leg re-center masih +0,004161 SOL. Posisi scanner paralel yang rugi berada di luar chain itu.

Dalam 24h pertama, 14 root-chain / 50 closed legs menghasilkan −0,005563 SOL. Sampai cutoff, **20 root-chain / 64 closed legs +0,000032 SOL** sebelum biaya wallet. Jadi mematikan semua re-center belum didukung agregat; biaya churn dan dua tail loss harus ditangani. Tidak ada compounding close dalam journal window ini.

Circuit breaker saat ini menambah `rebalance_pnl` hanya ketika akan melakukan re-center dan nilainya berasal dari mark sebelum settlement; loss terminal yang menutup run tidak otomatis masuk tally itu. Evaluasi floor berikutnya perlu total semua leg root-chain yang terukur, tanpa menyamakan mark dengan realized.

### 4. Timeout dan accounting belum selesai

Ada **dua re-center timeout 30 detik**, yang kemudian muncul sebagai posisi adopsi UBI/Noiz berlabel spot; jadi pesan "position stays closed" tidak boleh dipercaya tanpa cek chain. Ada **sembilan pesan auto-swap failed**, semuanya timeout 30 detik; tidak berarti sembilan transaksi pasti gagal, karena transaksi bisa sudah masuk. Total 20 baris timeout termasuk pengulangan pesan laporan.

Prioritas: rekonsiliasi tx/posisi/balance sebelum retry, jaga metadata mode/root pada adopsi, dan catat settlement swap/gas. Jangan menaikkan retry submit tanpa rekonsiliasi. Loop monitor tidak mengalami gap multi-jam: gap emisi start median 21,60s, p95 29,09s, maksimum 195,01s. Karena stdout buffering, metrik ini bukan latency eksekusi pasti.

## Momentum yang terlewat dibanding Meridian

| Contoh profit Meridian | Evidence Azimuth sebelum entry Meridian | Interpretasi |
|---|---|---|
| HODL +0,033423 SOL | Bot holders 30,2% > 30%, kemudian PvP guard | Safety rejection nyata; satu winner tidak cukup untuk mengendurkan gate. HODL sendiri sekitar 33,8% PnL Meridian 24h pertama. |
| TWINE +0,010790 SOL | Bundler volume 68,2% > 60%, ~14m sebelum entry | Bukan bug retry momentum; pool gagal safety gate. |
| NINA +0,014678 SOL | h1 −11,3%/−10,2% sekitar 29–30m sebelum entry Meridian | Kandidat recovery; perlu rekonstruksi eligibility saat entry, bukan menganggap semua profit Meridian bisa diambil. |
| INDEX +0,008001 SOL | Bundler volume 61,9% > 60% | Ada opportunity yang dilewatkan; pool INDEX juga menghasilkan loss Meridian −0,098646 SOL pada trade lain. Jangan memilih hanya winner sebagai benchmark. |

Kumulatif scanner turnover: 19.642 kandidat lolos screen, 8.040 kejadian cooldown, 7.790 dedup, 3.270 momentum rejects, 312 sent. Pulse: 6.921 lolos, 2.510 cooldown, 4.176 dedup, 201 sent. Ini kejadian berulang per cycle, bukan pool unik atau order; seluruh reject tidak boleh dilabeli missed profit.

## Snapshot terbuka dan keputusan

Saat fetch sekitar 14 September 13:02 WIB, Azimuth mempunyai NINA ~0,1 SOL; nested API flow menunjukkan unrealized sekitar +0,000343 SOL. Meridian mempunyai NEARKAT ~0,5 SOL, sekitar −0,000003 SOL. Angka ini tidak dimasukkan closed PnL. Field top-level Meridian seperti `pnlNative=-inputNative` dan `impermanentLoss=-inputValue` masih bertentangan dengan balances/nested PnL, sehingga diabaikan; bukan loss −100% yang nyata.

**Keep:** SOL-only entry, pulse, retry momentum tiap cycle, organic/bot/bundler guards, ukuran posisi, hard risk exits, dan fallback deterministik.

**Urutan perbaikan:** (1) precedence risk-floor/trailing vs indikator, (2) shared reservation mencegah duplicate entry dan re-center race, (3) timeout reconciliation plus provenance, (4) nilai ulang re-center per root-chain dengan biaya settlement, baru setelah itu tuning range/fee capture. Belum ada bukti untuk menaikkan size atau melonggarkan safety screening. Patch sebelumnya menyelesaikan mismatch strategi tetapi belum menyelesaikan sumber loss tersebut.

## Audit terjadwal

Timer benar-benar terpanggil **13 September 23:37:28 WIB**, tetapi CLI berhenti 5 detik kemudian dengan `You've hit your usage limit`. Jadi tidak ada report otomatis pada jadwal itu. Ini bukan timer yang tidak jalan dan bukan bot trading berhenti. Laporan ini adalah audit manual pengganti dengan cutoff yang tetap jelas. Bukti: `/home/ubuntu/azimuth-audits/review-24h-2026-09-13/run.jsonl`.

## Artefak dan source

- `positions.csv`: 228 close termasuk pembanding 24h sebelum deployment; 163 di periode pascapatch. Satu record Meridian sebelum deployment bernilai deposit 0, dicatat sebagai empty close, bukan trade bermodal; tidak memengaruhi total flow.
- `summary.json`, `log_summary.json`, `chains.json`, `overlapping_positions.json`, `errors.json`: hasil kalkulasi dan coverage.
- `azimuth_closed.json`, `meridian_closed.json`, journal snapshots, Meridian open snapshots, `scanner.log`, `monitor.log`: evidence mentah.
- `fetch.py`: fetch read-only dengan pagination dan retry terbatas, tidak menjalankan live backfill.
- `analyze.py`: rekonsiliasi flow (assert), dedup journal per position, window, grouping, CSV.
- Source root cause: `/home/ubuntu/azimuth/assets/skill/scripts/dlmm_monitor.py` (trailing ~1950, downtrend ~2200, timing ~2450, re-center ~2880); `/home/ubuntu/azimuth/assets/skill/scripts/dlmm_pipeline.py` (snapshot exposure ~1277, deploy ~1771). Tidak diubah dalam audit ini.
