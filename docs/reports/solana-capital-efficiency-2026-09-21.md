# Audit alokasi modal LP Solana: Azimuth vs Meridian

Snapshot utama: **20 September 2026 14:43:06–21 September 2026 14:43:06 WIB**. Konteks: tujuh hari berakhir pada waktu yang sama. Pemeriksaan read-only; tidak ada parameter, binary, posisi, atau transaksi live yang diubah.

**Kesimpulan: efisiensi fee Azimuth tertinggal dalam 24 jam terakhir, tetapi bukti tidak mendukung kesimpulan bahwa modal lebih kecil atau range terlalu lebar adalah satu-satunya penyebab. Selisih besar berasal dari kesempatan fee yang berbeda—terutama Stamp dan pool TYLER—ditambah modal yang lebih lama tidak menghasilkan fee, ketidakkonsistenan keputusan hold, dan kelemahan pencatatan/eksekusi. Meridian sendiri belum terbukti unggul secara konsisten setelah seluruh biaya dan konversi inventory.**

## Cakupan dan cara membaca

- Meridian API `/positions/open/raw` diambil langsung untuk kedua wallet; keduanya sukses. History posisi tertutup diambil dari seluruh halaman Meteora portfolio/position PnL untuk pool relevan: 70 pool Azimuth, 104 Meridian, nol fetch error.
- Journal Azimuth, arsip entry, hold journal, monitor dan scanner digabung dengan `lessons.json`, `state.json`, decision log, serta log Meridian dari `/home/ubuntu/meridian` (lokasi aktual instalasi).
- Semua **29 + 39 = 68 posisi tertutup terbaru** memiliki journal; 27/29 Azimuth punya arsip entry lokal, dua sisanya dilengkapi instruksi funding. Meridian punya state entry untuk 39/39. Instruksi funding berbentuk strategy ditemukan untuk 29/29 Azimuth dan 37/39 Meridian; dua Meridian lain memakai jalur funding berbeda, bukan dianggap tidak didanai.
- Dalam tujuh hari ada 219 account posisi tertutup Azimuth dan 334 Meridian; **lima account Meridian tidak memiliki deposit**, sehingga hanya 329 posisi Meridian yang didanai. Semua 553 account mendapat dossier, termasuk account kosong; jangan menjadikan account kosong sebagai trade sukses.
- Ada satu posisi Azimuth masih terbuka pada snapshot, BUTTHOLE; Meridian nol. Posisi terbuka dilaporkan terpisah agar tidak menghilangkan risiko yang belum direalisasi.
- [Dossier posisi 24 jam](solana-capital-efficiency-positions-24h-2026-09-21.md) merekonstruksi setiap posisi terbaru; [dossier posisi tujuh hari](solana-capital-efficiency-positions-7d-2026-09-21.md) mencakup semua account posisi tujuh hari; [posisi terbuka](solana-capital-efficiency-open-position-2026-09-21.md) dilaporkan terpisah.

Yang disebut **modal diputar** di bawah adalah jumlah deposit berulang, bukan modal awal wallet. Return terhadap deposit bukan ROI wallet. Fee adalah seluruh lifetime fee dari cohort posisi yang tutup dalam window; sebagian lifetime bisa dimulai sebelum window. Metrik fee per SOL-jam menggunakan lifetime cohort yang sama. Pengukuran waktu tanpa posisi menggunakan interval yang dipotong tepat pada window.

## Hasil utama, termasuk modal dan waktu

| Metrik 24 jam | Azimuth | Meridian |
|---|---:|---:|
| Posisi ditutup | 29 | 39 |
| Median modal per posisi | 0,12 SOL | 0,50 SOL |
| Total modal diputar | 3,3100 SOL | 19,5000 SOL |
| Fee LP, valuasi API | +0,015539 SOL | +0,313415 SOL |
| Perubahan principal sebelum fee | −0,015980 SOL | −0,163866 SOL |
| PnL LP, sebelum gas/konversi inventory | **−0,000442 SOL** | **+0,149548 SOL** |
| Fee / modal diputar | **0,4695%** | **1,6073%** |
| Fee per SOL-jam cohort | 79,77 bps | 294,61 bps |
| Median holding time | 30,72 menit | 11,50 menit |
| Median downside coverage | 35,46% | 35,46% |
| Median jumlah bin | 45 | 47 |
| Fee <1 bp modal | 10/29 | 17/39 |
| Fee lebih kecil dari gas posisi yang terhubung | 10/29 | 13/39 |
| Waktu tanpa LP aktif | 11,02 jam | 7,73 jam |
| Rata-rata modal didepositkan sepanjang window | 0,0802 SOL | 0,4331 SOL |
| Gas semua transaksi wallet dalam window | 0,000829 SOL | 0,001954 SOL |

Fee absolut Meridian 20,17× Azimuth dapat didekomposisi secara aritmetis menjadi **5,89× modal diputar × 3,42× fee per modal**. Ini bukan atribusi kausal: pool, waktu entry, sizing, dan risiko berbeda. Bahkan pada pool yang disentuh keduanya, hasil tetap berbeda, tetapi waktu entry tidak identik sehingga bukan eksperimen A/B.

**Keunggulan fee harian sangat terkonsentrasi:** Stamp menghasilkan 0,139465 SOL fee dan TYLER 0,101116 SOL, gabungan **76,8% seluruh fee Meridian**. Stamp menyumbang **76,5% PnL LP** Meridian. Setelah kedua token dikeluarkan dari masing-masing bot, fee/modal menjadi **Azimuth 0,4443% vs Meridian 0,4414%**. Ini analisis sensitivitas sesudah kejadian, bukan alasan untuk hanya memilih token yang sudah diketahui menang.

Konteks tujuh hari mengubah gambaran: fee/modal Azimuth **0,9215%**, Meridian **0,9091%**; PnL LP/modal masing-masing **+0,2371% dan +0,1674%**. Fee per SOL-jam tetap lebih tinggi di Meridian, **240,01 vs 157,37 bps**, konsisten dengan holding time yang lebih singkat. Data tujuh hari juga mencakup gangguan Redis Azimuth tanggal 14–15 September; pada 24 jam terbaru tidak ditemukan NOAUTH. Karena itu, tidak tepat menyebut strategi Meridian selalu lebih baik berdasarkan hari terakhir saja.

## Penjelasan keputusan dan pola per posisi

### 1. Stamp: kesempatan terlewat nyata, kesalahan filter belum terbukti

Meridian masuk lima kali pukul **02:35, 02:46, 02:58, 03:15, 03:30 WIB**, mengalokasikan total deposit berulang 2,5 SOL; PnL LP gabungan +0,114348 SOL. Azimuth baru masuk pukul **05:03** dan re-center **05:18**, total deposit 0,26 SOL; PnL LP +0,002217 SOL.

Namun log scanner Azimuth yang tersedia saat keputusan awal menunjukkan alasan risiko yang konkret:

- 02:15:59: bundler volume **66,4%**, melampaui batas 60%.
- 02:49:58: perubahan harga 5m **−3,2%**, melewati guard −3%.
- 02:50:59: bundler volume **71,4%**.
- 03:20:59: perubahan 5m **−13,6%**.

Jadi missed momentum terutama terlihat sebagai perbedaan toleransi risiko dan waktu entry, bukan bukti scanner mati. Melonggarkan batas hanya karena Meridian kemudian profit adalah hindsight. Uji yang layak adalah cohort kandidat yang ditolak sebelum mengetahui hasil, lengkap dengan peluang rug dan biaya eksekusi; data ini belum merupakan uji tersebut.

Entry Azimuth pertama memakai 45 bin, downside 35,46%; child memakai 21 bin, 18,05%. Keduanya keluar OOR ke sisi SOL dan mendapat fee. Re-center ini berguna secara outcome, tetapi entry signal pada child diwarisi dari induk, sehingga tidak membuktikan bahwa kondisi terbaru dinilai ulang.

### 2. TYLER: fee tier tinggi tidak menjamin fee capture tinggi

Azimuth `H5BKrq8j…`, entry **01:17:34**, memakai pool `7U1LVkLo…`, base fee **5%**, deposit 0,1 SOL. Fee 0,000210 SOL, PnL LP +0,000203 SOL. Meridian `EDhZ5pPJ…`, entry **01:22:05**, memilih pool `5zwSxWKt…`, base fee **1%**, deposit 0,5 SOL; fee **0,101116 SOL**.

Journal keputusan Meridian saat entry secara eksplisit membandingkan fee/TVL kedua pool: **2,33 vs 1,53**, memilih pool 1%. Dengan demikian ada bukti keputusan pemilihan pool berbasis aktivitas/yield, bukan sekadar memilih fee tier terbesar. Angka ini adalah perbandingan dalam snapshot Meridian; tidak boleh dibandingkan langsung dengan snapshot Azimuth 4,5 menit lebih awal atau timeframe berbeda.

Risikonya juga nyata: pada withdrawal, principal Meridian seluruhnya menjadi token. API mencatat principal −0,129790 SOL dan PnL LP **−0,028674 SOL**, sedangkan swap 7 detik kemudian menghasilkan 0,405847 SOL; setelah fee SOL yang diterima, hasil sebelum gas **+0,006963 SOL**. Selisih valuasi token +0,035638 SOL tidak bisa otomatis disebut slippage positif: mark API, perubahan harga, dan harga eksekusi belum dipisahkan. Kasus ini juga menunjukkan journal “Trailing TP” dan final PnL API tidak cukup untuk menilai kualitas exit.

### 3. SCRIBE: loss entry awal, exit risiko masuk akal, timeout bukan bukti swap gagal

Azimuth `6R5SXYr5…` masuk **18:17:50**, deposit 0,1 SOL, TVL snapshot sekitar $11.006, volatility feed 6,250, range **−550…−506**, downside 35,46%. Saat exit, journal sudah mengamati 5m **−13,5%** dan PnL mark −1,51%; hard risk exit punya dasar pada informasi saat itu. **Tidak perlu mengetahui recovery berikutnya untuk membenarkan exit risiko.**

Posisi tutup setelah 3,6 menit; withdrawal memiliki porsi nilai token sekitar **51,4%**. Fee +0,001759 SOL tidak menutup divergence principal −0,005792 SOL; PnL LP −0,004034 SOL. Log menyatakan auto-swap timeout 30 detik, tetapi transaksi `2Z2NWUcy…` berhasil menjual tepat 10.690,233156 token menjadi **0,051843812 SOL**, **65 detik** setelah close. Hasil dalam SOL sebelum gas adalah **−0,002370260 SOL**.

Meridian masuk pool yang sama **12 menit 34 detik kemudian**, setelah snapshot pasar berubah, dengan range lebih lebar 76 bin/52,59%, lalu memperoleh PnL LP +0,006945 SOL. Perbandingan ini tidak membuktikan bahwa Azimuth seharusnya menahan posisi loss; waktu entry dan harga berbeda. Yang terbukti perlu dibenahi adalah status eksekusi: timeout harus berstatus belum terkonfirmasi sampai rekonsiliasi transaksi, bukan final gagal.

### 4. FLAME: hold yang bertentangan dengan geometri range

Azimuth `9q8JShPq…` masuk **12:43:04**, 0,1 SOL, range **−733…−680**, batas atas sekitar **0,000004434434 SOL/token**. Pada snapshot terakhir sebelum hold pukul **13:10:54**, harga pool sudah sekitar **0,000004578047**, yaitu **di atas batas atas**, OOR 19,9 menit, fee posisi nol.

Alasan hold 15 menit memakai momentum 5m +3,81% dan 1h +6,20%, lalu menyebut harga kembali menuju range. Untuk bid ladder di bawah harga, **kenaikan harga justru menjauh dari range**. Kekeliruan penalaran ini dapat diketahui pada saat hold dibuat, tanpa memakai harga masa depan. Posisi akhirnya tutup pukul 13:26:32, total 43,47 menit, fee nol. PnL principal hampir nol tidak membuat alokasi ini efisien: ada gas dan waktu modal tidak menghasilkan.

Journal close juga mencatat `ai_holds: 0`, padahal hold journal dan monitor menunjukkan hold aktif. Hal yang sama terjadi pada fone. Karena itu evaluasi “AI hold vs no hold” tidak boleh hanya memakai kolom `ai_holds` pada close journal.

### 5. JEANPHIL dan baton: inventory drift serta keputusan berbasis angka yang tidak konsisten

JEANPHIL `GSduza2k…` bertahan 61,8 menit, selalu in-range pada sampel monitor yang teramati. Fee **0,001725 SOL**, tetapi principal turun **0,002391 SOL** dan PnL LP **−0,000666 SOL**. Porsi nilai token withdrawal sekitar 23%. Close karena stale re-pin memakai peak **+1,11%**; journal pada saat yang sama mencatat `pnl_sol` **−0,000485 SOL**. Ini contoh konkret denominasi yang berbeda di jalur keputusan, bukan tanda posisi menghasilkan profit dalam SOL.

baton `EBvE3rLZ…` bertahan **137,9 menit**, fee **0,002919 SOL**, principal −0,004269 SOL; setelah exact-match swap hasil sebelum gas **−0,001639895 SOL**. Pada exit sudah ada 1h −10,8% dan risk-floor PnL. Ini menunjukkan fees gagal mengimbangi inventory exposure. Data belum membuktikan waktu optimal untuk exit lebih dini; diperlukan pengukuran fee pace dan inventory yang konsisten pada tick-tick sebelumnya.

## Diagnosis range, distribusi, dan modal

**Active-bin placement:** tidak ditemukan selisih batas atas range terhadap active-bin snapshot/instruksi untuk 29 Azimuth dan 39 Meridian pada cohort terbaru. Semua deposit terbaru bermula single-sided SOL. Tidak ada bukti salah sisi token atau wrong-bin placement sistematis pada cohort ini. Ini validasi instruksi/range, bukan jaminan active bin tidak bergerak antara quote, submit, dan inclusion.

**Bentuk likuiditas:** kedua bot memakai BidAsk satu sisi. Desain ini memiliki sedikit modal dekat harga aktif dan lebih banyak pada bin lebih dalam; kenaikan harga melewati batas atas membuat posisi tetap SOL dan berhenti menangkap fee. Memperlebar range ke bawah tidak menyelesaikan upward OOR. Konsep ini konsisten dengan [SDK resmi Meteora](https://github.com/MeteoraAg/docs/blob/main/developer-guides/dlmm/typescript-sdk/examples.mdx) dan implementasi SDK lokal.

Model linear SDK pada **45 bin** hanya menempatkan sekitar **0,0966%** modal di active bin dan **1,4493%** pada lima bin terdekat. Pada ticket 0,12 SOL, lima bin tersebut hanya sekitar **0,001739 SOL**. Ini model distribusi nominal, bukan snapshot historis share aktual. BidAsk mengurangi pembelian dekat puncak, tetapi dapat terlalu menyebarkan modal untuk strategi yang ingin keluar dalam beberapa menit. Karena Meridian memakai bentuk yang sama dan median width hampir identik, bentuk tersebut belum terbukti menjadi penyebab utama selisih antarkedua bot.

**Re-center Azimuth mengubah mandat:** deployment normal menargetkan downside sekitar 35%, sedangkan turnover re-center memakai konstanta **20 bin**, sekitar 18,05% pada step 100. Ada lima child re-center terbaru: TIPPED dan Stamp positif, ZEBRA kecil positif, baton dan CHILLHOUSE nyaris nol/negatif. Range child tidak mengikuti floor 20% jalur entry normal dan snapshot signal diwarisi. Ini inkonsistensi implementasi yang terukur; bukan bukti bahwa semua re-center harus dihapus.

**Modal idle:** Azimuth tidak mempunyai LP aktif selama 11,02 dari 24 jam vs Meridian 7,73 jam. Waktu tanpa LP tidak semuanya kesalahan—filter risiko, cooldown, dan cadangan transaksi punya fungsi. Selain itu, modal di dalam LP belum tentu aktif menghasilkan fee. Tidak tersedia NAV historis lengkap per tick untuk menghitung persentase seluruh kekayaan yang idle.

Pemeriksaan saldo sesudah snapshot menunjukkan **0,366320 SOL bebas** Azimuth dan **1,682226 SOL bebas** Meridian. Azimuth memiliki 83 token accounts dengan 0,124958 SOL lamports; Meridian 150 dengan 0,226761 SOL. Lamports account adalah modal tertahan/rent, **bukan otomatis loss**, dan umumnya baru bisa direklamasi ketika account dapat ditutup. Angka ini bukan NAV: masih ada LP terbuka dan inventory token. Modal awal yang sama tidak berarti modal saat ini sama, dan menaikkan ticket tidak memperbaiki fee efficiency dengan sendirinya.

## Bug dan keterbatasan pengukuran yang terbukti

1. **Satuan slippage LP salah pada kedua bot.** Azimuth `dlmm_executor.js` meneruskan `slippageBps=1000` sebagai `slippage` SDK. SDK `initializePositionAndAddLiquidityByStrategy` mengharapkan **persen**, sehingga 1.000 bps (10%) seharusnya menjadi `10`. Meridian jalur non-wide juga mengirim `1000`, walaupun jalur chunkable memakai `10`. Instruksi blockchain mengonfirmasi toleransi **1.000/1.250/800 bin** pada step 100/80/125, bukan sekitar 10/13/8 bin. Ini bug proteksi dengan toleransi 100× terlalu besar, **bukan bukti slippage aktual sebesar itu terjadi**. Karena dialami keduanya, tidak sendirian menjelaskan gap performa.
2. **Azimuth primary monitor mencampur % USD dan nilai SOL.** `get_meteora_portfolio_positions()` memakai `pnlPctChange` untuk `pnl_pct` tetapi `pnlSol` untuk PnL nominal; fallback executor memakai `pnlSolPctChange`. Dengan target pertumbuhan SOL, trigger stop/trailing/peak dapat berubah menurut jalur data dan perubahan harga SOL/USD. Primary juga mengulang PnL tingkat pool untuk tiap position pada pool tersebut; aman hanya bila invariant satu posisi/pool benar-benar berlaku.
3. **Timeout swap belum direkonsiliasi sebagai status transaksi.** SCRIBE terbukti landed walau log gagal. Perlu membedakan submitted/unknown/confirmed/failed dan mendasarkan ledger pada signature.
4. **Hold direction dan hold journal tidak konsisten.** FLAME memberi contoh penalaran arah salah; kolom `ai_holds=0` tidak mencerminkan event yang tersimpan.
5. **Range efficiency Meridian bukan cumulative time-in-range.** `minutes_in_range = minutesHeld - minutesOOR`, dengan `minutesOOR` hanya dari `out_of_range_since` terakhir. Episode OOR sebelumnya yang sempat kembali in-range tidak dijumlahkan. Angka 100% di journal tidak membuktikan seluruh lifetime efektif.
6. **Raw API open memiliki field yang saling bertentangan.** BUTTHOLE raw menampilkan legacy `currentValue=0`, `liquidity=0`, `impermanentLoss=-13,409997 USD`, tetapi payload yang sama mempunyai `valueNative=0,119991908 SOL`, inventory nyata, fee 0,000023771 SOL, dan nested SOL PnL +0,000015705 SOL. Menganggap field legacy itu sebagai IL aktual akan menghasilkan diagnosis palsu.

Trace source: Azimuth `assets/skill/scripts/dlmm_executor.js:314,321`, `dlmm_monitor.py:50,604,2920`, `dlmm_pipeline.py:947,962`; Meridian `tools/dlmm.js:834,850,1988,2101`. Source checkout Azimuth saat audit HEAD `0b77a72` dengan perubahan lokal pengguna; audit ini tidak menganggap file sekarang identik dengan semua versi yang pernah live selama tujuh hari. Instruksi transaksi dipakai untuk memverifikasi perilaku yang benar-benar dikirim.

## IL, execution cost, dan batas klaim profit

Semua posisi funded terbaru masuk dalam SOL saja. Maka `withdrawal principal SOL-valued − deposit SOL` merupakan **divergence terhadap HOLD SOL pada mark API sebelum fee**. Ini mencakup efek inventory yang dibeli sepanjang lintasan harga dan valuasi exit; bukan cara memisahkan sempurna “IL murni” dari trend, adverse selection, atau mark error. Rumus IL constant-product 50:50 tidak diterapkan ke posisi DLMM ini.

Untuk transaksi konversi, exact-match mensyaratkan satu mint, jumlah withdrawal+fee token cocok, waktu paling jauh 30 menit setelah close, dan hanya satu kandidat swap. Klasifikasi API transaction type tidak dipercaya sebagai satu-satunya filter: swap SCRIBE diberi label `CLOSE_ACCOUNT` tetapi token flow menunjukkan swap.

| Rekonsiliasi yang benar-benar terisolasi | Azimuth | Meridian |
|---|---:|---:|
| Posisi terbaru dengan hasil SOL terisolasi, termasuk yang tidak menyisakan token | 13/29 | 20/39 |
| PnL LP API subset yang sama | −0,004181 SOL | +0,052292 SOL |
| PnL sesudah konversi, sebelum gas subset | −0,002807 SOL | +0,084793 SOL |
| Setelah gas yang terhubung subset | −0,003167 SOL | +0,083406 SOL |
| Exact token-swap match dalam subset | 2 | 11 |

**Subset ini tidak representatif otomatis dan tidak boleh diekstrapolasi menjadi profit seluruh wallet.** Swap lain mencampur dust dari posisi sebelumnya, atau token belum dikonversi. Selisih mark vs swap tidak dipaksakan menjadi “slippage”: quote pada saat submit dan timestamp mark yang presisi tidak tersedia.

Dalam tujuh hari, subset exact/no-token Azimuth 75 posisi mempunyai API PnL +0,041711 SOL, menjadi +0,004410 SOL setelah konversi sebelum gas. Meridian 174 posisi mempunyai API PnL −0,006250 SOL, menjadi −0,064602 SOL. Ini menunjukkan pentingnya accounting inventory pada **keduanya**, bukan kesimpulan bahwa profit seluruh wallet negatif/positif sesuai subset.

Seluruh history transaksi yang ditarik mencapai sebelum awal window; ada 748 transaksi Azimuth dan 1.235 Meridian dalam tujuh hari. Tidak ada transactionError pada response yang diterima. Ini tidak berarti tidak ada submission gagal: transaksi yang tidak pernah masuk chain tidak muncul. Tidak ditemukan pembayaran baru ke account bin-array pada instruksi init yang berhasil didekode; label `INITIALIZE_BIN_ARRAY` pada enhanced API dapat mencakup transaksi yang juga menyetor modal, sehingga total pengeluaran transaksi berlabel itu **bukan biaya rent**.

## Pemeriksaan seluruh hipotesis

| Hipotesis | Penilaian berdasarkan bukti |
|---|---|
| Incorrect liquidity range selection | Inkonsistensi entry normal vs re-center terbukti; range optimal setiap entry belum dapat ditentukan. |
| Incorrect active-bin placement | Tidak ditemukan pada instruksi/snapshot cohort terbaru; actual inclusion drift tidak lengkap. |
| Overly narrow liquidity | Re-center 20 bin menurunkan coverage menjadi 18%; belum terbukti penyebab loss utama. |
| Overly wide liquidity | Ada tradeoff terhadap fee concentration; median range kedua bot sama, sehingga bukan diagnosis utama gap. |
| Poor distribution across bins | Model BidAsk sangat sedikit modal dekat active bin; exact per-bin historical share tidak tersedia. |
| Bad concentration weighting | Hipotesis masuk akal untuk horizon pendek; tidak ada counterfactual replay yang membuktikan bobot alternatif unggul. |
| Excessive inventory imbalance | Exit SCRIBE, baton, ZEBRA, JEANPHIL menunjukkan akumulasi token; Meridian TYLER mencapai 100% token principal. |
| Asset price trend exposure | Terbukti pada inventory drift dan snapshot dump/downtrend; bukan semua loss disebut IL. |
| Volatility regime mismatch | Entry memakai angka volatility feed; tidak ada kalibrasi probabilitas range pada holding horizon. Azimuth normal width terutama tetap 35%. |
| Insufficient fee capture | Terbukti secara normalized 24h, tetapi sensitif pada Stamp/TYLER; tidak konsisten untuk keseluruhan 7d. |
| Excessive rebalance frequency | Lima child Azimuth terbaru, beberapa hampir tanpa fee. Besarnya opportunity cost alternatif belum diukur. |
| Rebalance too late | FLAME hold saat OOR memberi bukti keputusan pelepasan modal tidak tepat arah; waktu optimal lain belum diketahui. |
| Rebalance too early | Close stale JEANPHIL berbasis umur/peak patut ditinjau; outcome negatif tidak membuktikan hold lebih lama akan lebih baik. |
| Unnecessary repositioning | Ada round-trip dengan fee di bawah gas; menilai kelayakan ex ante butuh expected position fee dan cost, belum tersimpan. |
| Transaction/execution costs | Gas dihitung; rent account dipisahkan dari loss. Overhead relatif ticket kecil lebih besar. |
| Slippage | Bug satuan LP terbukti; actual slippage tidak dapat diisolasi dari price movement/mark tanpa quote archive. |
| Divergence/impermanent loss | Divergence vs HOLD SOL dapat dihitung pada exit API marks; IL murni terpisah tidak teridentifikasi. |
| Idle capital | 11,02 jam tanpa LP Azimuth, ditambah modal OOR; sebagian adalah keputusan risiko yang disengaja. |
| Poor capital utilization | Fee/SOL-jam Azimuth lebih rendah; FLAME nol fee selama 43,47 menit adalah contoh konkret. |
| Incorrect pool selection | TYLER menunjukkan pool 1% menangkap fee jauh lebih besar daripada pool 5%; ada bukti komparasi entry Meridian. |
| Bad fee-tier selection | Tier saja tidak cukup; volume, depth, fee yield, dan execution depth harus dibandingkan bersamaan. |
| Liquidity migrating away | Tidak dapat dibuktikan: TVL entry/exit bukan history liquidity per bin atau capital migration. |
| Incorrect volatility assumptions | Tidak ada kalibrasi sigma/horizon; komentar “daily volatility” tidak menjadi bukti bahwa feed adalah sigma harian. |
| Stale oracle/market state | Field API bertentangan dan mode PnL berbeda terbukti; latency oracle/slot age historis belum tersedia. |
| Implementation/execution bugs | Satuan slippage, PnL denomination, timeout reconciliation, hold logging dan range-efficiency ditemukan. |
| Unavoidable market movement | Shock setelah entry tidak diketahui sebelumnya; bagian residual belum bisa dibedakan dari adverse selection tanpa data path/quotes. |

## Prioritas perbaikan dan bagian yang dipertahankan

**P0 — perbaiki konsistensi eksekusi dan accounting dahulu:** konversi bps→persen pada adapter LP dan uji encoded `maxActiveBinSlippage`; gunakan PnL SOL yang sama di primary/fallback/peak/risk limits; rekonsiliasi timeout lewat signature; jangan menilai close sebagai wallet profit sebelum inventory selesai dihitung. Ini memberi proteksi dan pengukuran yang benar sebelum tuning strategi.

**P1 — perbaiki keputusan alokasi yang bisa dinilai saat itu:** hold harus memeriksa arah OOR terhadap range dan fee aktual posisi; samakan pencatatan event hold; re-center harus menyimpan snapshot baru serta mengevaluasi coverage dalam persen, biaya, dan expected fee untuk horizon berikutnya. TTL/umur posisi sendiri bukan bukti bahwa reposisi layak.

**P2 — evaluasi pool selection dan distribusi:** bandingkan semua pool untuk token yang sama memakai timeframe sama, fee per active liquidity, executable depth, dan biaya keluar. Uji bobot yang lebih dekat active bin dengan data replay/shadow sebelum live; jangan menaikkan ticket atau melemahkan filter bundler/momentum hanya untuk meniru satu kemenangan Meridian.

**Keep:** single-sided SOL entry dengan orientasi benar, dump/downtrend risk exits, guard terhadap duplicate exposure dan deploy serialization, pemeriksaan biaya bin-array, serta batas risiko kandidat. Audit terakhir tidak memberi dasar untuk melepas guard tersebut.

Tidak ada jaminan profit konsisten dari data ini. Langkah berikut yang paling kuat bukan meningkatkan frekuensi trade, melainkan menghilangkan inkonsistensi pengukuran/eksekusi dan mengoptimalkan **fee bersih per modal aktif per waktu dengan batas inventory risk**.
